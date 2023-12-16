import os.path

import pytest

from src.device import add_device_entry, does_device_exist, DeviceEntry
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


@pytest.mark.parametrize("device, expectation", [
    (
            {
                "name": "r1",
                "username": "",
                "password": "",
                "device_options": {}
            },
            True
    ), (
            {
                "name": "r2",
                "username": "",
                "password": "",
                "device_options": {}
            },
            True
    )
])
def test_insert_device(create_new_test_db, device, expectation):
    add_device_entry(DeviceEntry(**device), KEEPASS_TEST_DB_PATH, KEEPASS_TEST_PASSWORD)
    device_name = device["name"]
    assert does_device_exist(device_name, KEEPASS_TEST_DB_PATH, KEEPASS_TEST_PASSWORD) == expectation
