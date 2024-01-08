import os
from typing import List

from pykeepass import pykeepass
from rich.prompt import Prompt

from NetworkCommander.device import Device

DEVICE_GROUP_NAME = "device"


class KeepassDB:
    def __init__(self, keepass_db_path, keepass_password=None):
        self._keepass_db_path = keepass_db_path
        self._keepass_password = keepass_password
        if not self._keepass_password:
            self._keepass_password = Prompt.ask("🔑 enter keepass database master password", password=True)

    def __enter__(self):
        if not os.path.isfile(self._keepass_db_path):
            self._kp = pykeepass.create_database(self._keepass_db_path, password=self._keepass_password)
        else:
            self._kp = pykeepass.PyKeePass(self._keepass_db_path, password=self._keepass_password)
        return self._kp

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_val:
            self._kp.save()


def convert_device_entry_to_device(device_entry: pykeepass.Entry) -> Device:
    device_json = convert_device_to_json(device_entry)
    device_entry = Device(**device_json)
    return device_entry


def get_all_devices(kp: pykeepass.PyKeePass) -> List[Device]:
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    devices = [convert_device_entry_to_device(device) for device in device_group.entries]
    return devices


def does_device_exist(device_name: str, kp: pykeepass.PyKeePass) -> bool:
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    devices = kp.find_entries(group=device_group, title=device_name)
    return bool(devices)


def remove_device(device_name: str, kp: pykeepass.PyKeePass) -> None:
    if not does_device_exist(device_name, kp):
        raise Exception(f"{device_name} doesn't exist in db")
    device_entries = get_device_entries(device_name, kp)
    for device_entry in device_entries:
        kp.delete_entry(device_entry)


def get_device_entries(device_name, kp):
    if not does_device_exist(device_name, kp):
        raise Exception(f"{device_name} doesn't exist in db")
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    device_entries = kp.find_entries(group=device_group, title=device_name)
    return device_entries


def add_device_entry(device: Device, kp: pykeepass.PyKeePass) -> None:
    entry_title = device.name
    if does_device_exist(entry_title, kp):
        raise Exception(f"{entry_title} already exist in db")

    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]

    username = device.username
    password = device.password
    new_entry = kp.add_entry(device_group, entry_title, username, password)

    optional_data = {"host": device.host, "device_type": device.device_type}

    if device.port:
        optional_data["port"] = device.port
    for key, val in optional_data.items():
        new_entry.set_custom_property(key, val, True)


def convert_device_to_json(entry: pykeepass.Entry) -> dict[str, str]:
    device_options = {
        **entry.custom_properties,
    }
    device_options = {
        **device_options,
        "username": entry.username,
        "password": entry.password,
        "name": entry.title
    }
    if not device_options["username"]:
        device_options["username"] = ""
    if not device_options["password"]:
        device_options["password"] = ''

    return device_options
