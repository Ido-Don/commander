import os.path
import shutil

import mimesis
import pykeepass
import pytest

from networkcommander.init import create_new_keepass_db
from networkcommander.keepass import KeepassDB, add_device_entry, get_all_device_entries, get_device_tags, \
    does_device_exist
from mocks import get_test_device, get_tag_list, POSSIBLE_TAGS

KEEPASS_PASSWORD = "123"
POSSIBLE_NAMES = list(POSSIBLE_TAGS)
internet = mimesis.Internet()
generic = mimesis.Generic()
hardware = mimesis.Hardware()
POPULATED_DB_PATH = "populated_db.kdbx"


def populate_db(keepass_db_path: str):
    if os.path.isfile(keepass_db_path):
        os.remove(keepass_db_path)
    create_new_keepass_db(keepass_db_path, KEEPASS_PASSWORD)
    with KeepassDB(keepass_db_path, KEEPASS_PASSWORD) as kp:
        for _ in range(300):
            device = get_test_device()
            tags = get_tag_list()
            add_device_entry(kp, device, tags)


class TestKeepass:
    @pytest.fixture
    def populated_db(self) -> str:
        if os.path.isfile(POPULATED_DB_PATH):
            return POPULATED_DB_PATH
        populate_db(POPULATED_DB_PATH)
        return POPULATED_DB_PATH

    def test_keepass_db_creation(self):
        test_db_path = "test_db.kdbx"
        with KeepassDB(test_db_path, KEEPASS_PASSWORD):
            assert os.path.isfile(test_db_path)

    def test_keepass_db_insertion(self, populated_db):
        insertion_test_kdbx = "insertion_" + populated_db
        shutil.copyfile(populated_db, insertion_test_kdbx)

        device = get_test_device()
        kp = pykeepass.PyKeePass(insertion_test_kdbx, KEEPASS_PASSWORD)
        add_device_entry(kp, device)
        entry = kp.find_entries(title=device.name)[0]
        assert entry.title == device.name
        assert entry.password == device.password
        assert entry.username == device.username
        assert entry.get_custom_property("host") == device.host
        assert entry.get_custom_property("port") == str(device.optional_parameters['port'])
        assert entry.get_custom_property("device_type") == str(device.device_type)

    def test_keepass_db_insertion_with_tag(self, populated_db):
        # set up test environment
        insertion_test_kdbx = "insertion_tag_" + populated_db
        shutil.copyfile(populated_db, insertion_test_kdbx)

        device = get_test_device()
        tags = ["tag1", 'tag2']

        kp = pykeepass.PyKeePass(insertion_test_kdbx, KEEPASS_PASSWORD)

        # preform the operation
        add_device_entry(kp, device, tags)

        # find out if it was successful
        entry = kp.find_entries(title=device.name)[0]
        assert entry.title == device.name
        assert entry.password == device.password
        assert entry.username == device.username
        assert entry.get_custom_property("host") == device.host
        assert entry.get_custom_property("port") == str(device.optional_parameters['port'])
        assert entry.get_custom_property("device_type") == str(device.device_type)
        assert entry.tags == tags

    def test_db_selection(self, populated_db):
        device = get_test_device()
        test_db = "selection_" + populated_db
        create_new_keepass_db(test_db, KEEPASS_PASSWORD)

        kp = pykeepass.PyKeePass(test_db, KEEPASS_PASSWORD)
        add_device_entry(kp, device)

        devices = get_all_device_entries(kp)
        assert devices == [device]

    def test_db_selection_with_tags(self, populated_db):
        test_db = "selection_tags_" + populated_db
        shutil.copyfile(populated_db, test_db)

        kp = pykeepass.PyKeePass(test_db, KEEPASS_PASSWORD)
        device = get_test_device()
        tags = [generic.random.choice(POSSIBLE_TAGS)]
        add_device_entry(kp, device, tags)

        devices = get_all_device_entries(kp, set(tags))
        assert device in devices

    def test_get_device_tags(self, populated_db):
        kp = pykeepass.PyKeePass(populated_db, KEEPASS_PASSWORD)
        tags = get_device_tags(kp)
        assert tags == set(POSSIBLE_TAGS)

    def test_does_device_exist_false(self, populated_db):
        """
        this test check rather does_device_exist will catch that an entry is not in the db
        """
        test_db = "exist_" + populated_db
        shutil.copyfile(populated_db, test_db)
        kp = pykeepass.PyKeePass(test_db, KEEPASS_PASSWORD)

        # delete some random entry
        entry_to_delete = generic.random.choice(kp.entries)
        entry_to_delete_title = entry_to_delete.title
        entries_to_delete = kp.find_entries(title=entry_to_delete_title)
        for entry in entries_to_delete:
            kp.delete_entry(entry)

        # check if the random entry is still in the db
        assert not does_device_exist(kp, entry_to_delete_title)

    def test_does_device_exist_true(self, populated_db):
        """
        this test checks if the does_device_exist can find an entry that is in the database
        """
        kp = pykeepass.PyKeePass(populated_db, KEEPASS_PASSWORD)
        print(kp.entries)

        entry = generic.random.choice(kp.entries)
        assert does_device_exist(kp, entry.title)
