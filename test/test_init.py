import json
import logging
import os
import sys
from logging import Logger

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem, OSType

from networkcommander.config import config, COMMANDER_FOLDER, DEVICE_GROUP_NAME
from networkcommander.init import delete_project_files, create_new_keepass_db, is_file_json
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
def fake_filesystem(fs: FakeFilesystem):  # pylint:disable=invalid-name
    """Variable name 'fs' causes a pylint warning. Provide a longer name
    acceptable to pylint for use in tests.
    """
    return fs


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


def init_file_system(fake_filesystem: FakeFilesystem):
    fake_filesystem.os = OSType.WINDOWS
    create_blank_database()


def test_delete_project_files(fake_filesystem):
    init_file_system(fake_filesystem)
    create_fake_commander_folder(COMMANDER_FOLDER)
    delete_project_files(COMMANDER_FOLDER, fake_logger)
    assert not os.path.exists(COMMANDER_FOLDER)


def test_create_new_keepass_db(fake_filesystem):
    init_file_system(fake_filesystem)
    root_path = str(fake_filesystem.root.path)
    keepass_db_path = os.path.join(root_path, KEEPASS_DATABASE_FILE_NAME)
    create_new_keepass_db(keepass_db_path, KEEPASS_PASSWORD)
    assert os.path.exists(keepass_db_path)
    with KeepassDB(keepass_db_path, KEEPASS_PASSWORD) as kp:
        groups = kp.find_groups(name=DEVICE_GROUP_NAME)
        assert groups
        assert len(groups) == 1
        first_group = groups[0]
        assert first_group.name == DEVICE_GROUP_NAME

        entries = kp.entries
        assert not entries


def test_is_file_json(fake_filesystem):
    init_file_system(fake_filesystem)
    test_dictionary = {
        "hello": 1,
        "world": 2,
        "commander": [
            "is",
            "the",
            "best"
        ]
    }
    json_file_path = "json_file.json"
    with open(json_file_path, "w+") as json_file:
        json.dump(test_dictionary, json_file)
    assert is_file_json(json_file_path)

    not_json_file_path = "not_json_file.json"
    with open(not_json_file_path, "w+") as not_json_file:
        not_json_file.write("askdjljnasdkjnlsnf;jnjoi12nkj1o}{}")
    assert not is_file_json(not_json_file_path)
