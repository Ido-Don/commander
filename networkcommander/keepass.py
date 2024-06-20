"""
this file contains all of the functions that interact with keepass objects
"""

from itertools import filterfalse
import os
from logging import Logger
from typing import Callable, List, Any, Optional, Tuple, Set, Iterable

import pykeepass
import pykeepass.entry
from pykeepass import pykeepass
from rich.prompt import Prompt

from networkcommander.config import DEVICE_GROUP_NAME
from networkcommander.device import Device, DeviceType

REQUIRED_DEVICE_PROPERTIES = ["device_type", "host"]


class KeepassDB:
    """
    A class for creating connections to a KeePass database.

    Usage:
        Use with a context manager (with KeepassDB(...) as kp).
    """

    def __init__(self, keepass_db_path: str, keepass_password: str):
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
        if not self._kp:
            raise ValueError("kp must have a value in order to properly exit")
        if not exc_val:
            self._kp.save()

    @staticmethod
    def prompt_for_password():
        """
        Prompt the user for the KeePass database master password.

        :return: The master password for the KeePass database.
        """
        password = Prompt.ask(
            "enter keepass database master password", password=True)
        return password


def get_all_entries(kp: pykeepass.PyKeePass, logger: Logger) -> Tuple[pykeepass.Entry, ...]:
    """
    this function retrieves all entries and return them in a tuple
    :param kp: the keepass database object
    :param logger: the logger this function log massages to
    :return: a tuple containing all the entries in the kp object
    """
    logger.debug(f"retrieving all entries from keepass: {kp.filename}")
    device_group = get_device_group(kp)
    entries: List[pykeepass.Entry] = device_group.entries
    if not entries:
        logger.debug("no entries were found")
        entries = []
    tuple_entries = (*entries,)
    logger.debug(f"retrieved {len(tuple_entries)} entries")
    return tuple_entries


def get_device_group(kp: pykeepass.PyKeePass) -> pykeepass.Group:
    """
    this function returns the primary group named DEVICE_GROUP_NAME
    """
    primary_group = kp.find_groups(name=DEVICE_GROUP_NAME, first=True)
    if not primary_group:
        raise LookupError(
            f"group {DEVICE_GROUP_NAME} doesn't exist in keepass database")
    assert isinstance(primary_group, pykeepass.Group)
    return primary_group


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

    non_existent_device_properties = tuple(filter(
        lambda required_property: required_property not in custom_properties,
        REQUIRED_DEVICE_PROPERTIES
    ))

    if any(non_existent_device_properties):
        raise ValueError(
            f"there are no {', '.join(non_existent_device_properties)} in {name}.")

    device_type = DeviceType(custom_properties["device_type"])
    host = custom_properties["host"]

    def key_in_required_properties(pair: Tuple[Any, Any]) -> bool:
        key = pair[0]
        return key not in REQUIRED_DEVICE_PROPERTIES

    optional_parameters = dict(
        filter(key_in_required_properties, custom_properties.items()))
    device = Device(name, username, password, host,
                    device_type, optional_parameters)
    return device


def is_entry_tagged(tag: str):
    """
    this function returns a function which checks if an entry is tagged by a specific tag
    :param tag: a string that may be in the tags in entry
    """
    def inner(entry: pykeepass.Entry) -> bool:
        if not entry:
            return False
        if not tag:
            return True
        if not entry.tags:
            return False
        return tag in entry.tags

    return inner


def is_entry_tagged_by_tags(tags: Set[str]) -> Callable[[pykeepass.Entry], bool]:
    """
    this function return a function that checks 
    if an entry is tagged by all the tags in argument tags.
    the entry must have all the tags in order to return true.

    :param tags: a set of strings representing the tags to search
    :Returns: function which checks if an entry is tagged by the tags.
    """
    def inner(entry: pykeepass.Entry) -> bool:
        if not entry:
            return False
        if not tags:
            return True
        if not entry.tags:
            return False
        return all(tag in entry.tags for tag in tags)

    return inner


def does_device_exist(kp: pykeepass.PyKeePass, device_name: str) -> bool:
    """
    Check if a device with the given name exists in the KeePass database.

    :param kp: The connection to the KeePass database.
    :param device_name: The name of the device to check.
    :Returns: True if the device exists, False otherwise.
    """
    device_group = get_device_group(kp)
    devices = kp.find_entries(group=device_group, title=device_name)
    return bool(devices)


def remove_device(kp: pykeepass.PyKeePass, device_name: str) -> None:
    """
    Remove all devices from the KeePass database that based on the name.

    :param kp: The connection to the KeePass database.
    :param device_name: The name of the device to remove.
    :Raises: LookupError if the device does not exist in the database.
    """
    if not does_device_exist(kp, device_name):
        raise LookupError(f"{device_name} doesn't exist in db")

    device_group = get_device_group(kp)
    device_entries = kp.find_entries(group=device_group, title=device_name)

    if not device_entries:
        raise LookupError(f"{device_name} doesn't exist in db")

    for device_entry in device_entries:
        kp.delete_entry(device_entry)


def add_device_entry(
        kp: pykeepass.PyKeePass,
        device: Device,
        tags: Optional[List[str]] = None
) -> None:
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

    device_group = get_device_group(kp)

    username = normalize_input(device.username)
    password = normalize_input(device.password)

    new_entry = kp.add_entry(device_group, entry_title,
                             username, password, tags=tags)

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


def untag_entry(entry: pykeepass.Entry, tag: str) -> None:
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


def entries_to_devices(entries: Iterable[pykeepass.Entry]) -> Tuple[Device, ...]:
    """
    this function converts the entry Iterable given to a tuple of devices.

    :param entries: the entries
    :return: a device tuple from the entries given
    """
    return tuple(entry_to_device(entry) for entry in entries)


def filter_entries_by_tags(all_entries: Iterable[pykeepass.Entry], tags: Set) -> Tuple[pykeepass.Entry, ...]:
    """
    filter entries by the given tags.
    every entry must have every tag in order to return it.

    :param all_entries: the entries to filter on
    :param tags: the tags
    :return: a tuple with the relevant entries
    """
    return tuple(filter(is_entry_tagged_by_tags(tags), all_entries))


def is_entry_title_in_titles(titles: Set[str]):
    """
    this function return a function that checks 
    if an entry's title is in the titles set.

    :param tags: a set of strings representing the titles to search
    :Returns: function which checks if an entry's title is in titles.
    """
    def inner(entry: pykeepass.Entry):
        if not entry:
            return False
        if not titles:
            return False
        return entry.title in titles

    return inner


def filter_entries_by_titles(
    entries: Iterable[pykeepass.Entry],
    titles: Set[str]
) -> Tuple[pykeepass.Entry, ...]:
    return tuple(filter(is_entry_title_in_titles(titles), entries))


def filter_entries_by_title_not_in_titles(
        entries: Iterable[pykeepass.Entry],
        titles: Set[str]
) -> Tuple[pykeepass.Entry, ...]:
    """
    """
    return tuple(filterfalse(is_entry_title_in_titles(titles), entries))
