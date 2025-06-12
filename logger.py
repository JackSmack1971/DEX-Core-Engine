import logging

LOGGER_NAME = "dex_bot"

_def_logger = logging.getLogger(LOGGER_NAME)
if not _def_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    _def_logger.addHandler(handler)
    _def_logger.setLevel(logging.INFO)

logger = _def_logger

__all__ = ["logger"]

