import os

from networkcommander.commander_logging import commander_logger

HOME_FOLDER = os.path.expanduser("~")
COMMANDER_FOLDER = os.path.join(HOME_FOLDER, '.commander')
USER_CONFIG_FILE = os.path.join(COMMANDER_FOLDER, ".commanderconfig")
DEFAULT_KEEPASS_DB_PATH = os.path.join(COMMANDER_FOLDER, 'db.kdbx')
DEFAULT_LOG_FILE_PATH = os.path.join(HOME_FOLDER, ".commander/commander_logs.log")
config = {
    "commander_directory": COMMANDER_FOLDER,
    'keepass_db_path': DEFAULT_KEEPASS_DB_PATH,
    "max_worker": 60,
    "default_device_type": "cisco_ios",
    "optional_parameters": {
        "ssh_strict": True,
        "system_host_keys": True
    },
    "logging_file_level": "INFO",
    "logger_name": "commander",
    "log_file_path": DEFAULT_LOG_FILE_PATH
}


def load_user_config():
    """
    Load configuration settings from the user-specific configuration file.
    and update the application's configuration accordingly that lives in the config variable.

    Note: The configuration file is expected to be in JSON format.
    """
    print("load config")
    commander_logger.info("loading user config from %s", USER_CONFIG_FILE)
    if os.path.isfile(USER_CONFIG_FILE):
        commander_logger.debug("starting to open file located at %s", USER_CONFIG_FILE)
        with open(USER_CONFIG_FILE, encoding="UTF-8") as json_file:
            commander_logger.debug("successfully opened file located at %s", USER_CONFIG_FILE)
            file_content = json_file.read()
            if not file_content:
                commander_logger.debug("file %s had no data", USER_CONFIG_FILE)
                return
            commander_logger.debug("loading json", USER_CONFIG_FILE)
            user_custom_config = json.loads(file_content)
            config.update(user_custom_config)
            commander_logger.info("finished loading user config")


load_user_config()
