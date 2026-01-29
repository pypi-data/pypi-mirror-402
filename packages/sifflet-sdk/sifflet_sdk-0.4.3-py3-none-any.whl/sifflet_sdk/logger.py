import logging


def get_logger() -> logging.Logger:
    """
    Returns a logger with the specified name.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="%X")

    return logging.getLogger("sifflet")


logger: logging.Logger = get_logger()
