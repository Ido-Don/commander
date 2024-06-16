import os


HOME_FOLDER = os.path.expanduser("~")
COMMANDER_FOLDER_PATH = os.path.join(HOME_FOLDER, '.commander')
USER_CONFIG_FILE_PATH = os.path.join(COMMANDER_FOLDER_PATH, ".commanderconfig")
DEFAULT_KEEPASS_DB_PATH = os.path.join(COMMANDER_FOLDER_PATH, 'db.kdbx')
DEFAULT_LOG_FILE_PATH = os.path.join(HOME_FOLDER, ".commander/commander_logs.log")
config = {
    "commander_directory": COMMANDER_FOLDER_PATH,
    'keepass_db_path': DEFAULT_KEEPASS_DB_PATH,
    "config_file_path": USER_CONFIG_FILE_PATH,
    "max_worker": 60,
    "default_device_type": "cisco_ios",
    "optional_parameters": {
        "ssh_strict": True,
        "system_host_keys": True
    },
    "logging_file_level": "DEBUG",
    "logger_name": "commander",
    "log_file_path": DEFAULT_LOG_FILE_PATH
}
DEVICE_GROUP_NAME = "device"
