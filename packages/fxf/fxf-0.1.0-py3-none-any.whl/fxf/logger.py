import logging

_logger = logging.getLogger("fxf")
_logger.addHandler(logging.NullHandler())


def enable_logging(level="INFO", file=None):
    _logger.setLevel(level)

    formatter = logging.Formatter(
        "[FXF][%(levelname)s] %(message)s"
    )

    if file:
        handler = logging.FileHandler(file, encoding="utf-8")
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(formatter)
    _logger.handlers.clear()
    _logger.addHandler(handler)


def get_logger():
    return _logger