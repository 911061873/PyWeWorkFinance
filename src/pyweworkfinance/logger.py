import logging
import sys


def setup_logger():
    logger = logging.getLogger("pyweworkfinance")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("{asctime} [{levelname:^7}] : {message}", style="{")
    handler.setFormatter(
        formatter,
    )
    logger.addHandler(handler)
    return logger


logger = setup_logger()
