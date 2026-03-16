import logging
import os

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(level: str | None = None) -> None:
    """Configures root logging once so module logs are visible in console.

    Args:
        level: Optional log level override (e.g. ``"DEBUG"``, ``"INFO"``).

    Example usage:
        >>> configure_logging("INFO")
    """
    resolved_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, resolved_level, logging.INFO),
        format=_DEFAULT_FORMAT,
        force=False,
    )


def get_logger(name: str) -> logging.Logger:
    """Returns a module logger and ensures baseline logging is configured.

    Args:
        name: Logger name, usually ``__name__``.

    Returns:
        Configured ``logging.Logger`` instance.

    Example usage:
        >>> logger = get_logger(__name__)
        >>> logger.info("Logger ready")
    """
    configure_logging()
    return logging.getLogger(name)
