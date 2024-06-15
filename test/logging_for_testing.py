import logging
import sys
from logging import Logger

fake_logger = Logger("fake_logger_commander", "DEBUG")
stream_handler = logging.StreamHandler(sys.stdout)
stream_formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")
fake_logger.addHandler(stream_handler)

stream_handler.setFormatter(stream_formatter)