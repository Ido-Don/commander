import os

HOME_FOLDER = os.path.expanduser("~")
USER_CONFIG_FILE = os.path.join(HOME_FOLDER, "commander-config.json")
DEFAULT_COMMANDER_FOLDER = os.path.join(HOME_FOLDER, '.commander')
DEFAULT_KEEPASS_DB_PATH = os.path.join(DEFAULT_COMMANDER_FOLDER, 'db.kdbx')
config = {
    "commander_directory": DEFAULT_COMMANDER_FOLDER,
    'keepass_db_path': DEFAULT_KEEPASS_DB_PATH,
    "max_worker": 30,
    "default_device_type": "cisco_ios"
}
