from datetime import timezone, datetime, timedelta, date
import logging
import re
import traceback
import uuid
from time import time

import aiohttp
from aiohttp import ClientResponse
from logging_loki import LokiHandler
from pythonjsonlogger import jsonlogger

from tp_helper.types.env_type import EnvType


class ExceptionFormatterFilter(logging.Filter):
    """Filter that formats exceptions into JSON structure and adds to extra."""
    
    def filter(self, record: logging.LogRecord):
        """Format exception info into structured JSON if present."""
        # Check if there's exception info
        if record.exc_info and record.exc_info[0] is not None:
            exc_type, e, exc_traceback = record.exc_info
            
            # Get error message
            err_msg = str(e) if e else ""
            
            # Build error structure
            err = {
                "error": str(e),
                "error_message": err_msg,
            }
            
            # Extract traceback
            if exc_traceback:
                tb = traceback.extract_tb(exc_traceback)
                if tb:
                    # Convert FrameSummary objects to dicts for JSON serialization
                    tb_list = []
                    for frame in tb:
                        tb_list.append({
                            "filename": frame.filename,
                            "lineno": frame.lineno,
                            "name": frame.name,
                            "line": frame.line
                        })
                    err["traceback"] = "".join(tb_list)
                    
                    # Add last traceback line
                    last = tb[-1]
                    err["last_tb_line"] = f"{last.filename}:{last.lineno} — {last.name} → {last.line}"
            
            # Add error structure directly to record so it appears in JSON output
            # This will be included in the formatted JSON log
            record.error = err
        
        return True


# class TaggedLogFilter(logging.Filter):
#     """Filter that wraps extra dict in tags key on LogRecord before handlers process it.
#
#     Filters run before handlers, ensuring tags are set on the LogRecord
#     before Loki or other handlers process it.
#     """
#
#     _STANDARD_ATTRS = {
#         'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
#         'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname',
#         'process', 'processName', 'relativeCreated', 'thread', 'threadName',
#         'exc_info', 'exc_text', 'stack_info', 'asctime', 'extra', 'tags',
#         'taskName'
#     }
#
#     def __init__(self, job: str | uuid.UUID | int | None = None):
#         """Initialize filter with optional job to add to tags."""
#         super().__init__()
#         self.job = job
#
#     def filter(self, record: logging.LogRecord):
#         """Transform the record by wrapping extra fields in tags."""
#         # Start with existing tags if present, or empty dict
#         if hasattr(record, 'tags') and isinstance(record.tags, dict):
#             tags = record.tags.copy()
#         else:
#             tags = {}
#
#         # Find all non-standard attributes (these come from extra parameter)
#         extra_fields = {k: v for k, v in record.__dict__.items()
#                         if k not in self._STANDARD_ATTRS}
#
#         # If user explicitly passed extra={"tags": {...}}, use that as base
#         if 'tags' in extra_fields and isinstance(extra_fields['tags'], dict):
#             tags.update(extra_fields['tags'])
#             # Remove 'tags' from extra_fields so we don't add it again
#             del extra_fields['tags']
#
#         # Add label to tags if provided (label takes precedence if already in tags)
#         if self.job:
#             tags['job'] = self.job
#
#         # Merge remaining extra fields into tags
#         if extra_fields:
#             tags.update(extra_fields)
#
#         # Set tags on record if we have any
#         if tags:
#             record.tags = tags
#
#         return True



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
    name: str | int,
    env: EnvType,
    job: str | uuid.UUID | int | None = None,
    filename: str = None,
    loki_handler: LokiHandler | None = None
) -> logging.Logger:
    formatter = jsonlogger.JsonFormatter(
        "{asctime}{levelname}{message}{env}",
        style="{",
        json_ensure_ascii=False,
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "message": "msg",
        },
        static_fields={
            "env": env
        }
    )

    # Настройка логгера
    logger = logging.getLogger(f"custom_logger_{name}")
    logger.setLevel(logging.DEBUG)

    # Add filter to format exceptions into JSON structure
    logger.addFilter(ExceptionFormatterFilter())
    
    # Add filter with optional label - label will be included in tags if provided
    # logger.addFilter(TaggedLogFilter(job=job))

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
