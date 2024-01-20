import os
from typing import List, Union

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


def entry_to_device(device_entry: pykeepass.Entry) -> Device:
    device_json = convert_entry_to_json(device_entry)
    device_entry = Device(**device_json)
    return device_entry


def get_all_device_entries(kp: pykeepass.PyKeePass, tags: List[str] = None) -> List[Device]:
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    if tags:
        devices_entries = kp.find_entries(group=device_group, tags=tags)
    else:
        devices_entries = device_group.entries
    devices = [entry_to_device(device_entry) for device_entry in devices_entries]
    return devices


def get_device_tags(kp: pykeepass.PyKeePass):
    tags = set()
    for entry in kp.entries:
        if entry.tags:
            tags.update(entry.tags)

    return tags


def does_device_exist(device_name: str, kp: pykeepass.PyKeePass) -> bool:
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    devices = kp.find_entries(group=device_group, title=device_name)
    return bool(devices)


def get_device(kp, device_name):
    entries = get_device_entries(kp, device_name)
    if len(entries) > 1:
        raise Exception(f"{device_name} has more then")
    entry = entries[0]
    device = entry_to_device(entry)
    return device


def remove_device(kp: pykeepass.PyKeePass, device_name: str) -> None:
    if not does_device_exist(device_name, kp):
        raise Exception(f"{device_name} doesn't exist in db")
    device_entries = get_device_entries(kp, device_name)
    for device_entry in device_entries:
        kp.delete_entry(device_entry)


def get_device_entries(kp: pykeepass.PyKeePass, device_name: str):
    if not does_device_exist(device_name, kp):
        raise Exception(f"{device_name} doesn't exist in db")
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    device_entries = kp.find_entries(group=device_group, title=device_name)
    return device_entries


def add_device_entry(kp: pykeepass.PyKeePass, device: Device, tags: List[str] = None) -> None:
    entry_title = device.name
    if does_device_exist(entry_title, kp):
        raise Exception(f"{entry_title} already exist in db")

    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]

    username = device.username
    password = device.password
    new_entry = kp.add_entry(device_group, entry_title, username, password, tags=tags)

    optional_data = {"host": device.host, "device_type": device.device_type}

    if device.port:
        optional_data["port"] = device.port
    for key, val in optional_data.items():
        new_entry.set_custom_property(key, str(val), True)


def convert_entry_to_json(entry: pykeepass.Entry) -> dict[str, Union[str, int]]:
    device_options = {
        **entry.custom_properties,
        "username": entry.username,
        "password": entry.password,
        "name": entry.title
    }
    if 'port' in device_options:
        if not device_options['port']:
            raise ValueError("port is defined in the entry but doesn't have any value")

        port = device_options['port']
        device_options['port'] = int(port)

    if not device_options["username"]:
        device_options["username"] = ""
    if not device_options["password"]:
        device_options["password"] = ''

    return device_options


def tag_device(kp: pykeepass.PyKeePass, device_tag: str, device_name: str):
    if not does_device_exist(device_name, kp):
        raise Exception(f"{device_name} doesn't exist in db")
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    device_entries = kp.find_entries(group=device_group, title=device_name)

    for device_entry in device_entries:
        tags = device_entry.tags
        if tags:
            tags += [device_tag]
        else:
            tags = [device_tag]
        device_entry.tags = tags


def untag_device(kp: pykeepass.PyKeePass, device_tag: str, device_name: str):
    if not does_device_exist(device_name, kp):
        raise Exception(f"{device_name} doesn't exist in db")
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    device_entries = kp.find_entries(group=device_group, title=device_name)

    for device_entry in device_entries:
        tags = device_entry.tags
        if not tags or device_tag not in tags:
            raise ValueError(f"device {device_name} is not tagged with {device_tag}")
        tags.remove(device_tag)
        device_entry.tags = tags
