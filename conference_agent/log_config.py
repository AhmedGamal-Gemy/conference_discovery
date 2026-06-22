"""Logging configuration: structlog to both console and rotating file.

Must be called BEFORE any submodule that uses structlog.get_logger().
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog


def configure_logging(log_file: str, max_bytes: int = 10_485_760, backup_count: int = 3, debug: bool = False) -> None:
    log_level = logging.DEBUG if debug else logging.INFO
    _use_json = not sys.stderr.isatty()

    _shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *_shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    _console_renderer = (
        structlog.processors.JSONRenderer()
        if _use_json
        else structlog.dev.ConsoleRenderer()
    )

    _console_handler = logging.StreamHandler(stream=sys.stdout)
    _console_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=_shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                _console_renderer,
            ],
        )
    )

    _log_path = Path(log_file)
    _log_path.parent.mkdir(parents=True, exist_ok=True)
    _file_handler = RotatingFileHandler(
        _log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    _file_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=_shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(_console_handler)
    root_logger.addHandler(_file_handler)
    root_logger.setLevel(log_level)

    # Fix uvicorn.access: propagate to root logger so file handler catches it
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = True
