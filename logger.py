from __future__ import annotations

import gzip
import logging
import os
import uuid
from contextvars import ContextVar
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from pythonjsonlogger import jsonlogger

LOGGER_NAME = "dex_bot"
LOG_FILE = os.getenv("LOG_FILE", "logs/dex_bot.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def _compress(src: str, dst: str) -> None:
    with open(src, "rb") as f_in, gzip.open(dst, "wb") as f_out:
        f_out.writelines(f_in)
    os.remove(src)


def _setup_handler() -> logging.Handler:
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    handler = TimedRotatingFileHandler(
        LOG_FILE, when="midnight", backupCount=30, encoding="utf-8"
    )
    handler.namer = lambda name: f"{name}.gz"
    handler.rotator = _compress
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(component)s %(correlation_id)s %(message)s %(metadata)s %(duration_ms)s %(trade_id)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(fmt)
    return handler


class _ExtraFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _correlation_id.get()
        record.metadata = getattr(record, "metadata", {})
        record.duration_ms = getattr(record, "duration_ms", 0)
        record.trade_id = getattr(record, "trade_id", "")
        return True


def _configure_root() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = _setup_handler()
        logger.addHandler(handler)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(handler.formatter)
        logger.addHandler(stream_handler)
        logger.setLevel(LOG_LEVEL)
        logger.addFilter(_ExtraFilter())
    return logger


_root_logger = _configure_root()


class ComponentAdapter(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        extra = self.extra.copy()
        extra.update(kwargs.get("extra", {}))
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(component: str) -> logging.Logger:
    return ComponentAdapter(_root_logger, {"component": component})


def set_correlation_id(cid: str | None = None) -> str:
    cid = cid or uuid.uuid4().hex
    _correlation_id.set(cid)
    return cid


__all__ = ["get_logger", "set_correlation_id"]
