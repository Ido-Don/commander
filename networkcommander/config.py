import os

HOME_FOLDER = os.path.expanduser("~")
COMMANDER_FOLDER = os.path.join(HOME_FOLDER, '.commander')
USER_CONFIG_FILE = os.path.join(COMMANDER_FOLDER, ".commanderconfig")
DEFAULT_KEEPASS_DB_PATH = os.path.join(COMMANDER_FOLDER, 'db.kdbx')
config = {
    "commander_directory": COMMANDER_FOLDER,
    'keepass_db_path': DEFAULT_KEEPASS_DB_PATH,
    "max_worker": 30,
    "default_device_type": "cisco_ios",
    "optional_parameters": {}
}
