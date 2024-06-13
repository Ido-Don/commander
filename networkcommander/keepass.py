import os
from typing import List, Any, Tuple, Set, Iterable

import pykeepass
import pykeepass.entry
from pykeepass import pykeepass
from rich.prompt import Prompt

from networkcommander.device import Device, DeviceType

DEVICE_GROUP_NAME = "device"


class KeepassDB:
    """
    A class for creating connections to a KeePass database.

    Usage:
        Use with a context manager (with KeepassDB(...) as kp).
    """

    def __init__(self, keepass_db_path, keepass_password):
        """
        Initialize KeepassDB with the path to the KeePass database and its password.

        :param keepass_db_path: Path to the KeePass database.
        :param keepass_password: Password for the KeePass database.
        """
        self._keepass_db_path = keepass_db_path
        self._keepass_password = keepass_password
        if not self._keepass_password:
            self._keepass_password = KeepassDB.prompt_for_password()
        self._kp = None

    def __enter__(self) -> pykeepass.PyKeePass:
        """
        return the KeePass database object when used as a context manager.

        :return: The connection to the KeePass database object.
        """
        if not os.path.isfile(self._keepass_db_path):
            self._kp = pykeepass.create_database(
                self._keepass_db_path,
                password=self._keepass_password
            )
        else:
            self._kp = pykeepass.PyKeePass(
                self._keepass_db_path,
                password=self._keepass_password
            )
        return self._kp

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Saves the KeePass database when exiting the context manager.

        :param exc_type: Exception type.
        :param exc_val: Exception value.
        :param exc_tb: Exception traceback.
        """
        if not exc_val:
            self._kp.save()

    @staticmethod
    def prompt_for_password():
        """
        Prompt the user for the KeePass database master password.

        :return: The master password for the KeePass database.
        """
        password = Prompt.ask("enter keepass database master password", password=True)
        return password


def get_all_entries(kp: pykeepass.PyKeePass) -> Tuple[pykeepass.Entry]:
    primary_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    entries = primary_group.entries
    if not entries:
        entries = []
    tuple_entries = tuple(entries)
    return tuple_entries


def normalize_input(value: Any) -> str:
    """
    Converts a truthy value to a string and a falsy value to an empty string.

    :param value: Any value that can be converted to a string.
    :Returns: The string representation of the value if it's truthy, otherwise an empty string.
    """
    if not value:
        return ""
    return str(value)


def entry_to_device(device_entry: pykeepass.Entry) -> Device:
    """
    Converts a KeePass entry to a Device object.

    :param device_entry: The KeePass entry representing the device.
    :Returns: The Device object.
    """
    name = normalize_input(device_entry.title)
    username = normalize_input(device_entry.username)
    password = normalize_input(device_entry.password)
    custom_properties = device_entry.custom_properties

    required_properties = ["device_type", "host"]
    non_existing_properties = [
        required_property not in custom_properties for required_property in required_properties
    ]
    if any(non_existing_properties):
        raise ValueError(f"there are no {', '.join(non_existing_properties)} in {name}.")

    device_type = DeviceType(custom_properties["device_type"])
    host = custom_properties["host"]

    def key_in_required_properties(pair: Tuple[Any, Any]):
        key = pair[0]
        return key not in required_properties

    optional_parameters = dict(filter(key_in_required_properties, custom_properties.items()))
    device_entry = Device(name, username, password, host, device_type, optional_parameters)
    return device_entry


def is_entry_tagged(tag: str):
    def inner(entry: pykeepass.Entry):
        if not entry:
            return False
        if not tag:
            return True
        if not entry.tags:
            return False
        return tag in entry.tags

    return inner


def is_entry_tagged_by_tag_set(tags: Set[str]):
    def inner(entry: pykeepass.Entry):
        if not entry:
            return False
        if not tags:
            return True
        if not entry.tags:
            return False
        return all((tag in entry.tags for tag in tags))

    return inner


def does_device_exist(kp: pykeepass.PyKeePass, device_name: str) -> bool:
    """
    Check if a device with the given name exists in the KeePass database.

    :param kp: The connection to the KeePass database.
    :param device_name: The name of the device to check.
    :Returns: True if the device exists, False otherwise.
    """
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    devices = kp.find_entries(group=device_group, title=device_name)
    return bool(devices)


def remove_device(kp: pykeepass.PyKeePass, device_name: str) -> None:
    """
    Remove a device from the KeePass database by its name.

    :param kp: The connection to the KeePass database.
    :param device_name: The name of the device to remove.
    :Raises: LookupError if the device does not exist in the database.
    """
    if not does_device_exist(kp, device_name):
        raise LookupError(f"{device_name} doesn't exist in db")

    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    device_entries = kp.find_entries(group=device_group, title=device_name)
    for device_entry in device_entries:
        kp.delete_entry(device_entry)


def add_device_entry(kp: pykeepass.PyKeePass, device: Device, tags: List[str] = None) -> None:
    """
    Add a device entry to the KeePass database.

    :param kp: The connection to the KeePass database.
    :param device: The Device object to add.
    :param tags: Optional list of tags to assign to the entry.
    :Raises: LookupError if a device with the same name already exists in the database.
    """
    entry_title = device.name
    if not entry_title:
        raise ValueError("devices must have a name...")

    if does_device_exist(kp, entry_title):
        raise LookupError(f"{entry_title} already exist in db")

    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]

    username = normalize_input(device.username)
    password = normalize_input(device.password)

    new_entry = kp.add_entry(device_group, entry_title, username, password, tags=tags)

    custom_properties = {
        "host": device.host,
        "device_type": device.device_type,
        **device.optional_parameters
    }
    for key, val in custom_properties.items():
        new_entry.set_custom_property(key, str(val), True)


def tag_entry(entry: pykeepass.Entry, tag: str) -> None:
    """
    add a tag to an entry
    :param entry: a database entry
    :param tag: the tag to be added to the entry
    """
    existing_tags = entry.tags
    if existing_tags:
        existing_tags += [tag]
    else:
        existing_tags = [tag]
    entry.tags = existing_tags


def untag_entry(entry: pykeepass.Entry, tag: str):
    """
    remove a tag from an entry
    :param entry: a database entry
    :param tag: the tag to be removed from the entry
    :raise LookupError: when the tag doesn't exist in the entry
    """
    tags = entry.tags
    if not tags or tag not in tags:
        raise LookupError(f"entry {entry.title} is not tagged with {tag}")
    tags.remove(tag)
    entry.tags = tags


def entries_to_devices(entries: Iterable[pykeepass.entry.Entry]) -> Tuple[Device, ...]:
    return tuple((entry_to_device(entry) for entry in entries))
