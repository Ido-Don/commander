import os
from typing import List, Union, Dict, Any, Tuple

import pykeepass
from pykeepass import pykeepass
from rich.prompt import Prompt

from networkcommander.device import Device, SupportedDevice

DEVICE_GROUP_NAME = "device"


class KeepassDB:
    """
    this class is made to create connections to keepass database.
    it should be used with "with" (with KeepassDB(...) as kp)
    """

    def __init__(self, keepass_db_path, keepass_password):
        self._keepass_db_path = keepass_db_path
        self._keepass_password = keepass_password
        if not self._keepass_password:
            self._keepass_password = KeepassDB.prompt_for_password()
        self._kp = None

    def __enter__(self):
        """
        it returns the original keepass database object.
        :return: the keepass connection object
        """
        if not os.path.isfile(self._keepass_db_path):
            self._kp = pykeepass.create_database(
                self._keepass_db_path,
                password=self._keepass_password
            )
        else:
            self._kp = pykeepass.PyKeePass(self._keepass_db_path, password=self._keepass_password)
        return self._kp

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_val:
            self._kp.save()

    @staticmethod
    def prompt_for_password():
        """
        ask the user for a keepass password
        :return: the password
        """
        password = Prompt.ask("enter keepass database master password", password=True)
        return password


def normalize_input(value: Any) -> str:
    """
    this convert a truthy value to a string and a falsy value to an empty string.
    :param value: any value that can be converted to string
    :return: the string if that value is truthy
    """
    if not value:
        return ""
    return str(value)


def entry_to_device(device_entry: pykeepass.Entry) -> Device:
    name = normalize_input(device_entry.title)
    username = normalize_input(device_entry.username)
    password = normalize_input(device_entry.password)
    custom_properties = device_entry.custom_properties

    required_properties = ["device_type", "host"]
    """
    this variable is here to
    """
    non_existing_properties = [
        required_property not in custom_properties for required_property in required_properties
    ]
    if any(non_existing_properties):
        raise ValueError(f"there are no {', '.join(non_existing_properties)} in {name}.")

    device_type = SupportedDevice(custom_properties["device_type"])
    host = custom_properties["host"]

    def key_in_required_properties(pair: Tuple[Any, Any]):
        key, value = pair
        return key not in required_properties

    optional_parameters = dict(filter(key_in_required_properties, custom_properties.items()))
    device_entry = Device(name, username, password, host, device_type, optional_parameters)
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


def does_device_exist(kp: pykeepass.PyKeePass, device_name: str) -> bool:
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    devices = kp.find_entries(group=device_group, title=device_name)
    return bool(devices)


def get_device(kp: pykeepass.PyKeePass, device_name: str):
    entries = get_device_entries(kp, device_name)
    if len(entries) > 1:
        raise LookupError(f"{device_name} has more then 1 entry associated with it")
    entry = entries[0]
    device = entry_to_device(entry)
    return device


def remove_device(kp: pykeepass.PyKeePass, device_name: str) -> None:
    if not does_device_exist(kp, device_name):
        raise LookupError(f"{device_name} doesn't exist in db")
    device_entries = get_device_entries(kp, device_name)
    for device_entry in device_entries:
        kp.delete_entry(device_entry)


def get_device_entries(kp: pykeepass.PyKeePass, device_name: str):
    if not does_device_exist(kp, device_name):
        raise LookupError(f"{device_name} doesn't exist in db")
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    device_entries = kp.find_entries(group=device_group, title=device_name)
    return device_entries


def add_device_entry(kp: pykeepass.PyKeePass, device: Device, tags: List[str] = None) -> None:
    entry_title = device.name
    if does_device_exist(kp, entry_title):
        raise LookupError(f"{entry_title} already exist in db")

    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]

    username = device.username
    password = device.password
    new_entry = kp.add_entry(device_group, entry_title, username, password, tags=tags)

    custom_properties = {"host": device.host, "device_type": device.device_type, **device.optional_parameters}
    for key, val in custom_properties.items():
        new_entry.set_custom_property(key, str(val), True)


def tag_device(kp: pykeepass.PyKeePass, device_tag: str, device_name: str):
    if not does_device_exist(kp, device_name):
        raise LookupError(f"{device_name} doesn't exist in db")
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
    if not does_device_exist(kp, device_name):
        raise LookupError(f"{device_name} doesn't exist in db")
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    device_entries = kp.find_entries(group=device_group, title=device_name)

    for device_entry in device_entries:
        tags = device_entry.tags
        if not tags or device_tag not in tags:
            raise ValueError(f"device {device_name} is not tagged with {device_tag}")
        tags.remove(device_tag)
        device_entry.tags = tags


def get_existing_devices(kp: pykeepass.PyKeePass, devices: List[Device]):
    existing_devices = []
    for device in devices:
        if does_device_exist(kp, device.name):
            existing_devices.append(device)
    return existing_devices


def filter_non_existing_device_names(kp: pykeepass.PyKeePass, devices_names: List[str]):
    non_existing_devices = list(filter(
        lambda device_name: not does_device_exist(kp, device_name),
        devices_names
    ))
    return non_existing_devices
