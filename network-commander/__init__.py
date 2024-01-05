import os
import __version__
HOME_FOLDER = os.path.expanduser("~")
if "COMMANDER_DIRECTORY" in os.environ:
    COMMANDER_DIRECTORY = os.environ["COMMANDER_DIRECTORY"]
else:
    COMMANDER_DIRECTORY = os.path.join(HOME_FOLDER, ".network-commander")
KEEPASS_DB_PATH = os.path.join(COMMANDER_DIRECTORY, "db.kdbx")
