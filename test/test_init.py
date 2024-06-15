import json
import logging
import os
import sys
from logging import Logger

import pytest

from networkcommander.config import config, COMMANDER_FOLDER
from networkcommander.init import delete_project_files
from networkcommander.keepass import KeepassDB

fake_logger = Logger("fake_logger_commander", "DEBUG")
stream_handler = logging.StreamHandler(sys.stdout)
fake_logger.addHandler(stream_handler)

stream_formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")
stream_handler.setFormatter(stream_formatter)

COMMANDER_CONFIG_FILE_NAME = ".commanderconfig"
KEEPASS_DATABASE_FILE_NAME = "db.kdbx"
KEEPASS_PASSWORD = '123'

blank_database_data = open(r"C:\code\network-commander\test\blank_database.kdbx", 'rb').read()
blank_database_paths = [
    'C:\\Users\\עידו\\AppData\\Local\\Programs\\Python\\Python310\\Lib\\site-packages\\pykeepass\\blank_database.kdbx',
    "C:\\venv\\python3.10\\Lib\\site-packages\\pykeepass\\blank_database.kdbx"
]


@pytest.fixture
def fake_filesystem(fs):  # pylint:disable=invalid-name
    """Variable name 'fs' causes a pylint warning. Provide a longer name
    acceptable to pylint for use in tests.
    """
    yield fs


def create_fake_commander_folder(directory_path: str):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
    commander_config_file_path = os.path.join(directory_path, COMMANDER_CONFIG_FILE_NAME)
    if not os.path.exists(commander_config_file_path):
        with open(commander_config_file_path, "w+", encoding="UTF-8") as commander_config_file:
            json.dump(config, commander_config_file)
    keepass_database_file_path = os.path.join(directory_path, KEEPASS_DATABASE_FILE_NAME)
    if not os.path.exists(keepass_database_file_path):
        with KeepassDB(keepass_database_file_path, KEEPASS_PASSWORD):
            pass


def create_blank_database():
    for blank_database_path in blank_database_paths:
        os.makedirs(os.path.dirname(blank_database_path), exist_ok=True)
        with open(blank_database_path, "wb") as blank_database_file:
            blank_database_file.write(blank_database_data)


def test_delete_project_files(fake_filesystem):
    create_blank_database()
    create_fake_commander_folder(COMMANDER_FOLDER)
    delete_project_files(COMMANDER_FOLDER, fake_logger)
    assert not os.path.exists(COMMANDER_FOLDER)
