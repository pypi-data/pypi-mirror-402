import logging
import logging.config
from pathlib import Path

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | "
    "%(filename)s:%(lineno)d | %(name)s | %(message)s"
)

def configure_logging(log_file: Path | None = None, level: str = "INFO"):
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": level,
        }
    }

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": str(log_file),
            "formatter": "default",
            "level": level,
            "encoding": "utf-8",
        }

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": LOG_FORMAT
            }
        },
        "handlers": handlers,
        "root": {
            "handlers": list(handlers.keys()),
            "level": level,
        },
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str):
    return logging.getLogger(name)
