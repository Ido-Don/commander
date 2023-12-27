import os.path
from getpass import getpass
from typing import Dict
from pydantic import BaseModel
from pykeepass import pykeepass


class DeviceEntry(BaseModel):
    name: str
    username: str
    password: str
    device_options: Dict[str, str]


class DataBase:
    def __init__(self, keepass_db_path, keepass_password=None):
        self._keepass_db_path = keepass_db_path
        self._keepass_password = keepass_password
        if not self._keepass_password:
            self._keepass_password = getpass("enter keepass database master password: ")

    def __enter__(self):
        if not os.path.isfile(self._keepass_db_path):
            self._kp = pykeepass.create_database(self._keepass_db_path, password=self._keepass_password)
        else:
            self._kp = pykeepass.PyKeePass(self._keepass_db_path, password=self._keepass_password)
        return self._kp

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_val:
            self._kp.save()


def get_all_devices(kp: pykeepass.PyKeePass):
    device_group = kp.find_groups(name="devices")[0]
    devices = {device.title: get_device_options(device) for device in device_group.entries}
    return devices


def does_device_exist(device_name, kp: pykeepass.PyKeePass) -> bool:
    device_group = kp.find_groups(name="devices")[0]
    return device_name in [device.title for device in device_group.entries]


def add_device_entry(device_entry: DeviceEntry, kp: pykeepass.PyKeePass):
    entry_title = device_entry.name
    if does_device_exist(entry_title, kp):
        raise Exception(f"{entry_title} already exist in db")

    device_group = kp.find_groups(name="devices")[0]

    username = device_entry.username
    password = device_entry.password
    new_entry = kp.add_entry(device_group, entry_title, username, password)

    optional_data = device_entry.device_options
    for key, val in optional_data.items():
        new_entry.set_custom_property(key, val, True)


def get_device_options(entry: pykeepass.Entry):
    device_options = {**entry.custom_properties}
    username = entry.username
    if username:
        device_options["username"] = username

    password = entry.password
    if password:
        device_options["password"] = password
    return device_options
