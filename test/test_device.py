import os.path

import pytest

from src.device import add_device_entry, does_device_exist
from src.init import create_new_keepass_db

KEEPASS_TEST_DB_PATH = r"test.kdbx"
KEEPASS_TEST_PASSWORD = "T3st"


@pytest.fixture
def create_new_test_db():

    # remove old test db if exist
    if os.path.isfile(KEEPASS_TEST_DB_PATH):
        os.remove(KEEPASS_TEST_DB_PATH)

    # recreate the db
    create_new_keepass_db(KEEPASS_TEST_DB_PATH, KEEPASS_TEST_PASSWORD)


def test_insert_device(create_new_test_db):
    add_device_entry("r1", "", "", {"host": "127.0.0.1"}, KEEPASS_TEST_DB_PATH, KEEPASS_TEST_PASSWORD)
    assert does_device_exist("r1", KEEPASS_TEST_DB_PATH, KEEPASS_TEST_PASSWORD)
