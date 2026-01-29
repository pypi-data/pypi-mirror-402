import asyncio
import functools
import inspect
import traceback
from typing import Awaitable, Callable, ParamSpec, TypeVar

from tp_helper import get_full_class_name

P = ParamSpec("P")  # параметры оригинальной функции
R = TypeVar("R")  # возвращаемый тип оригинальной функции


def retry_forever(
    start_message: str,
    error_message: str,
    delay: int = 10,
    backoff: float = 1.2,
    max_delay: int = 60,
    discord_every: int = 3,
    ignore_exceptions: list[type[Exception | BaseException]] | None = None,
) -> Callable[
    [Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]
]:  # принимает и возвращает асинхронную функцию с исходной сигнатурой
    """
    Оборачивает только метод класса.
    """
    if ignore_exceptions is None:
        ignore_exceptions = [],

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        sig = inspect.signature(func)

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # --- Собираем контекст для подстановки в сообщения
            self = args[0] if args else None  # self итак уже есть в *args
            if self is None:
                raise ValueError(
                    "@retry_forever применяется только к методу класса, "
                    f"но {func.__qualname__} не принимает аргументов"
                )
            try:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                context = dict(bound.arguments)
            except Exception:
                context = {"self": self}

            str_context = {k: str(v) for k, v in context.items()}

            # --- Распаковываем self.*
            if "self" in context:
                self_obj = context["self"]
                try:
                    for attr in dir(self_obj):
                        if not attr.startswith("_"):
                            val = getattr(self_obj, attr)
                            if not callable(val):
                                str_context[attr] = str(val)
                except Exception:
                    pass

            # --- Лог старта
            try:
                self.logger.debug(start_message.format_map(str_context))
            except Exception:
                self.logger.debug(start_message)

            # --- Цикл повторов
            current_delay = delay
            retry_count = 0

            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if type(e) in ignore_exceptions:
                        raise e from e
                    retry_count += 1

                    str_context_with_exception = {
                        **str_context,
                        "e": str(e),
                        "retry_count": retry_count,
                    }

                    try:
                        err_msg = error_message.format_map(str_context_with_exception)
                    except Exception:
                        err_msg = error_message

                    self.logger.error(f"❌ {err_msg}")
                    self.logger.error(f"{get_full_class_name(e)}: {str(e)}")

                    tb = traceback.extract_tb(e.__traceback__)
                    if tb:
                        last = tb[-1]
                        self.logger.error(
                            f"📍 В {last.filename}:{last.lineno} — {last.name} → {last.line}"
                        )

                    if (
                        retry_count % discord_every == 0
                        and hasattr(self, "discord")
                        and callable(getattr(self.discord, "send_traceback_report", None))
                    ):
                        try:
                            await self.discord.send_traceback_report(e, err_msg)
                        except Exception as discord_error:
                            self.logger.warning(
                                f"⚠️ Ошибка при отправке в Discord: {discord_error}"
                            )

                    self.logger.info(
                        f"🔁 Повтор #{retry_count} через {current_delay:.1f} сек..."
                    )

                    await asyncio.sleep(current_delay)
                    current_delay = min(current_delay * backoff, max_delay)

        return wrapper

    return decorator
