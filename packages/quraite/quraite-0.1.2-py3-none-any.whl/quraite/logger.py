import logging
import os

_logger = logging.getLogger("quraite")
_logger.addHandler(logging.NullHandler())


def set_log_level(level: int | str) -> None:
    """
    Configure the root quraite logger programmatically.

    Args:
        level: Either a logging level integer or its string name (e.g. "INFO").
    """
    resolved_level: int
    if isinstance(level, str):
        try:
            resolved_level = getattr(logging, level.upper())
        except AttributeError as exc:
            raise ValueError(f"Invalid log level: {level}") from exc
    else:
        resolved_level = level

    _logger.setLevel(resolved_level)

    # Ensure a stream handler is attached so logs are emitted somewhere useful.
    if not any(
        isinstance(handler, logging.StreamHandler) for handler in _logger.handlers
    ):
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        _logger.addHandler(handler)


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger for quraite submodules.

    Args:
        name: Module name (typically __name__)

    Returns:
        A logging.Logger instance for the quraite package.
    """
    if name is None:
        return _logger

    if name.startswith("quraite"):
        return logging.getLogger(name)

    return logging.getLogger(f"quraite.{name}")


# Set level from environment variable if provided
_env_level = os.getenv("LOG_LEVEL") or "INFO"
try:
    set_log_level(_env_level)
except ValueError:
    pass
