from datetime import timezone, datetime, timedelta, date
import json
import logging
import re
from time import time
from typing import Any

import aiohttp
from aiohttp import ClientResponse
from logging_loki import LokiHandler


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


class JSONFormatter(logging.Formatter):
    """Кастомный форматтер для логирования в JSON формате."""
    
    def __init__(self, label: str = ""):
        super().__init__()
        self.label = label
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON формат."""
        log_data: dict[str, Any] = {
            "asctime": self.formatTime(record, self.datefmt),
            "levelname": record.levelname,
            "message": record.getMessage(),
        }
        
        # Добавляем лейбл, если он указан
        if self.label:
            log_data["label"] = self.label
        
        # Добавляем extra параметры, если они были переданы
        # Исключаем стандартные поля logging, чтобы не дублировать их
        standard_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName', 'relativeCreated',
            'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
            'asctime', 'label'
        }
        
        for key, value in record.__dict__.items():
            if key not in standard_fields:
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)


def get_logger(
    name: str | int = None, label: str = "", filename: str = None, loki_handler: LokiHandler | None = None
) -> logging.Logger:
    # Создание кастомного JSON форматтера
    formatter = JSONFormatter(label=label)

    # Настройка логгера
    logger = logging.getLogger(f"custom_logger_{name}")
    logger.setLevel(logging.DEBUG)

    # Создание обработчика (stdout)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    if loki_handler:
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
