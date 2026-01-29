import logging

_logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    if _logger.handlers:
        return

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)

    _logger.propagate = False


_setup_logging()
