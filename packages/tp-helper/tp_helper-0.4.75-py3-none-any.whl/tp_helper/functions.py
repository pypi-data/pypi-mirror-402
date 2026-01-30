from datetime import timezone, datetime, timedelta, date
import logging
import re
from time import time

import aiohttp
from aiohttp import ClientResponse
from logging_loki import LokiHandler
from pythonjsonlogger import jsonlogger

class TaggedLogFilter(logging.Filter):
    """Filter that wraps extra dict in tags key on LogRecord before handlers process it.

    Filters run before handlers, ensuring tags are set on the LogRecord
    before Loki or other handlers process it.
    """

    _STANDARD_ATTRS = {
        'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
        'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname',
        'process', 'processName', 'relativeCreated', 'thread', 'threadName',
        'exc_info', 'exc_text', 'stack_info', 'asctime', 'extra', 'tags'
    }

    def __init__(self, label: str = ""):
        """Initialize filter with optional label to add to tags."""
        super().__init__()
        self.label = label

    def filter(self, record):
        """Transform the record by wrapping extra fields in tags."""
        if hasattr(record, 'tags') and isinstance(record.tags, dict):
            tags = record.tags.copy()
        else:
            tags = {}

        extra_fields = {k: v for k, v in record.__dict__.items()
                        if k not in self._STANDARD_ATTRS}

        if 'tags' in extra_fields and isinstance(extra_fields['tags'], dict):
            tags.update(extra_fields['tags'])
            del extra_fields['tags']

        if self.label:
            tags['label'] = self.label

        if extra_fields:
            tags.update(extra_fields)

        if tags:
            record.tags = tags

        return True



def get_full_class_name(obj):
    module = obj.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return obj.__class__.__name__
    return module + "." + obj.__class__.__name__


def timestamp() -> int:
    return int(time())


def get_moscow_datetime():
    est_timezone = timezone(timedelta(hours=3))

    return datetime.now(est_timezone)


def get_moscow_date():
    return get_moscow_datetime().date()


def current_data_add(
        days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
):
    return date.today() + timedelta(
        days=days,
        seconds=seconds,
        microseconds=microseconds,
        milliseconds=milliseconds,
        minutes=minutes,
        hours=hours,
        weeks=weeks,
    )


def get_logger(
        name: str | int = None, label: str = "", filename: str = None, loki_handler: LokiHandler | None = None
) -> logging.Logger:
    formatter = jsonlogger.JsonFormatter("{asctime}{levelname}{message}{exc_info}", style="{", json_ensure_ascii=False)

    # Настройка логгера
    logger = logging.getLogger(f"custom_logger_{name}")
    logger.setLevel(logging.DEBUG)

    logger.addFilter(TaggedLogFilter(label=label))

    # Создание обработчика (stdout)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    if loki_handler:
        # Устанавливаем форматтер для LokiHandler, чтобы он отправлял JSON
        loki_handler.setFormatter(formatter)
        logger.addHandler(loki_handler)

    # all_handler = logging.FileHandler(filename="../logs/everything.txt", mode="a")
    # all_handler.setFormatter(formatter)
    # logger.addHandler(all_handler)

    # Создание обработчика (file out)
    if filename:
        fh = logging.FileHandler(filename=filename, mode="a")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    logger.addHandler(handler)

    return logger


def digits_only(v: str) -> str:
    if not re.fullmatch(r"\d+", v):
        raise ValueError("Must contain only digits")
    return v


def format_number(v: int) -> str:
    return f"{v:,}".replace(",", " ")


async def get_real_ip(proxy: str | None = None) -> tuple[ClientResponse, str]:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://ip.8525.ru", proxy=proxy) as response:
            return response, (await response.text()).strip()
