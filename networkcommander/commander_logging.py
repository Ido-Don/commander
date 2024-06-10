import logging
import uuid

from networkcommander.config import config

# we need a unique id to differentiate between commander runs
logging_id = uuid.uuid4()

commander_logger = logging.getLogger(config["logger_name"])
commander_logger.setLevel(config["logging_file_level"])

file_handler = logging.FileHandler(config["log_file_path"])

formatter = logging.Formatter(f'{logging_id} : %(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)

commander_logger.addHandler(file_handler)
