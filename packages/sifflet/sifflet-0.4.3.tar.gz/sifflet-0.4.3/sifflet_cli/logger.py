import logging

import click
from rich.logging import RichHandler


def get_logger() -> logging.Logger:
    """
    Returns a logger with the specified name.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="%X",
        handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click], markup=True)],
    )

    return logging.getLogger("sifflet")


logger: logging.Logger = get_logger()
