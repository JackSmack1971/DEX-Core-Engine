import logging
import uuid
from contextvars import ContextVar

LOGGER_NAME = "dex_bot"

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class _CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        record.correlation_id = _correlation_id.get()
        return True


_def_logger = logging.getLogger(LOGGER_NAME)
if not _def_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(correlation_id)s - %(message)s"
    )
    handler.setFormatter(formatter)
    _def_logger.addHandler(handler)
    _def_logger.setLevel(logging.INFO)
    _def_logger.addFilter(_CorrelationFilter())

logger = _def_logger

def set_correlation_id(cid: str | None = None) -> str:
    """Set the correlation ID for log context."""
    cid = cid or uuid.uuid4().hex
    _correlation_id.set(cid)
    return cid


__all__ = ["logger", "set_correlation_id"]

