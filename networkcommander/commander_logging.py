import logging
import sys
import uuid
from enum import Enum

from networkcommander.config import config

# we need a unique id to differentiate between commander runs
logging_id = uuid.uuid4()

commander_logger = logging.getLogger(config["logger_name"])
commander_logger.setLevel(config["logging_file_level"])

file_handler = logging.FileHandler(config["log_file_path"])
stream_handler = logging.StreamHandler(sys.stdout)

file_formatter = logging.Formatter(f'{logging_id} : %(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(file_formatter)

stream_formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")
stream_handler.setFormatter(stream_formatter)

commander_logger.addHandler(file_handler)


class LogLevel(str, Enum):
    NOTSET = "notset"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"

    def __str__(self):
        return self.value


def add_stream_handler(log_level: LogLevel):
    stream_handler.setLevel(log_level)
    commander_logger.addHandler(stream_handler)
    commander_logger.debug("added stream logger at log level %s", log_level)