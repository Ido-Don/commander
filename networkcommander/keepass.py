import os
from typing import List, Any, Tuple

import pykeepass
from pykeepass import pykeepass
from rich.prompt import Prompt

from networkcommander.device import Device, SupportedDevice

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

    device_type = SupportedDevice(custom_properties["device_type"])
    host = custom_properties["host"]

    def key_in_required_properties(pair: Tuple[Any, Any]):
        key = pair[0]
        return key not in required_properties

    optional_parameters = dict(filter(key_in_required_properties, custom_properties.items()))
    device_entry = Device(name, username, password, host, device_type, optional_parameters)
    return device_entry


def get_all_device_entries(kp: pykeepass.PyKeePass, tags: List[str] = None) -> List[Device]:
    """
    Retrieve all device entries from the KeePass database.

    :param kp: The connection to the KeePass database.
    :param tags: Optional list of tags to filter the entries.
    :Returns: A list of Device objects representing the retrieved entries.
    """
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    if tags:
        devices_entries = kp.find_entries(group=device_group, tags=tags)
    else:
        devices_entries = device_group.entries
    devices = list(map(entry_to_device, devices_entries))
    return devices


def get_device_tags(kp: pykeepass.PyKeePass):
    """
    Retrieve all unique device tags from the KeePass database.

    :param kp: The connection to the KeePass database.
    :Returns: A set containing all unique device tags.
    """
    tags = set()
    for entry in kp.entries:
        if entry.tags:
            tags.update(entry.tags)

    return tags


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


def get_device(kp: pykeepass.PyKeePass, device_name: str):
    """
    Retrieve a device from the KeePass database by its name.

    :param kp: The connection to the KeePass database.
    :param device_name: The name of the device to retrieve.
    :Returns: The Device object representing the retrieved device.
    """
    entries = get_device_entries(kp, device_name)
    if len(entries) > 1:
        raise LookupError(f"{device_name} has more then 1 entry associated with it")
    entry = entries[0]
    device = entry_to_device(entry)
    return device


def remove_device(kp: pykeepass.PyKeePass, device_name: str) -> None:
    """
    Remove a device from the KeePass database by its name.

    :param kp: The connection to the KeePass database.
    :param device_name: The name of the device to remove.
    :Raises: LookupError if the device does not exist in the database.
    """
    if not does_device_exist(kp, device_name):
        raise LookupError(f"{device_name} doesn't exist in db")
    device_entries = get_device_entries(kp, device_name)
    for device_entry in device_entries:
        kp.delete_entry(device_entry)


def get_device_entries(kp: pykeepass.PyKeePass, device_name: str):
    """
    Retrieve all entries of a device from the KeePass database by its name.

    :param kp: The connection to the KeePass database.
    :param device_name: The name of the device.
    :Returns: A list of pykeepass.Entry objects representing the retrieved device entries.
    :Raises: LookupError if the device does not exist in the database.
    """
    if not does_device_exist(kp, device_name):
        raise LookupError(f"{device_name} doesn't exist in db")
    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]
    device_entries = kp.find_entries(group=device_group, title=device_name)
    return device_entries


def add_device_entry(kp: pykeepass.PyKeePass, device: Device, tags: List[str] = None) -> None:
    """
    Add a device entry to the KeePass database.

    :param kp: The connection to the KeePass database.
    :param device: The Device object to add.
    :param tags: Optional list of tags to assign to the entry.
    :Raises: LookupError if a device with the same name already exists in the database.
    """
    entry_title = device.name
    if does_device_exist(kp, entry_title):
        raise LookupError(f"{entry_title} already exist in db")

    device_group = kp.find_groups(name=DEVICE_GROUP_NAME)[0]

    username = device.username
    password = device.password
    new_entry = kp.add_entry(device_group, entry_title, username, password, tags=tags)

    custom_properties = {
        "host": device.host,
        "device_type": device.device_type,
        **device.optional_parameters
    }
    for key, val in custom_properties.items():
        new_entry.set_custom_property(key, str(val), True)


def tag_device(kp: pykeepass.PyKeePass, device_tag: str, device_name: str):
    """
    Tag a device entry in the KeePass database with a specified tag.

    :param kp: The connection to the KeePass database.
    :param device_tag: The tag to assign to the device entry.
    :param device_name: The name of the device entry.
    :Raises: LookupError if the device does not exist in the database.
    """
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
    """
    Remove a tag from a device entry in the KeePass database.

    :param kp: The connection to the KeePass database.
    :param device_tag: The tag to remove from the device entry.
    :param device_name: The name of the device entry.
    :raises: LookupError if the device does not exist in the database.
             ValueError if the device is not tagged with the specified tag.
    """
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
    """
    Retrieve existing devices from the list of devices in the KeePass database.

    :param kp: The connection to the KeePass database.
    :param devices: A list of Device objects.
    :Returns: A list of Device objects representing the devices that already exist in the database.
    """
    existing_devices = []
    for device in devices:
        if does_device_exist(kp, device.name):
            existing_devices.append(device)
    return existing_devices


def filter_non_existing_device_names(kp: pykeepass.PyKeePass, devices_names: List[str]):
    """
    Filter out device names that do not exist in the KeePass database.

    :param kp: The connection to the KeePass database.
    :param devices_names: A list of device names to filter.
    :Returns: A list of device names that do not exist in the database.
    """
    non_existing_devices = list(filter(
        lambda device_name: not does_device_exist(kp, device_name),
        devices_names
    ))
    return non_existing_devices
