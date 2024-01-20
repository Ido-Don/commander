import os
__version__ = '0.2.3'
HOME_FOLDER = os.path.expanduser("~")
COMMANDER_DIRECTORY = os.path.join(HOME_FOLDER, ".commander")
KEEPASS_DB_PATH = os.path.join(COMMANDER_DIRECTORY, "db.kdbx")
