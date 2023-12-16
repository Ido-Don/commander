from typing import Dict
from pydantic import BaseModel
from pykeepass import pykeepass


class DeviceEntry(BaseModel):
    name: str
    username: str
    password: str
    device_options: Dict[str, str]


def get_all_devices(keepass_db_path, keepass_password):
    kp = pykeepass.PyKeePass(keepass_db_path, password=keepass_password)
    device_group = kp.find_groups(name="devices")[0]
    devices = {}
    for device in device_group.entries:
        device_options = get_device_options(device)
        device_title = device.title
        devices[device_title] = device_options
    return devices


def does_device_exist(device_name, keepass_db_path, keepass_password):
    kp = pykeepass.PyKeePass(keepass_db_path, password=keepass_password)
    device_group = kp.find_groups(name="devices")[0]
    return device_name in [device.title for device in device_group.entries]


def add_device_entry(device_entry: DeviceEntry, db_path, keepass_password):
    entry_title = device_entry.name
    if does_device_exist(entry_title, db_path, keepass_password):
        raise Exception(f"{entry_title} already exist in db")

    kp = pykeepass.PyKeePass(db_path, password=keepass_password)
    device_group = kp.find_groups(name="devices")[0]

    username = device_entry.username
    password = device_entry.password
    new_entry = kp.add_entry(device_group, entry_title, username, password)

    optional_data = device_entry.device_options
    for key, val in optional_data.items():
        new_entry.set_custom_property(key, val, True)
    kp.save()


def get_device_options(entry: pykeepass.Entry):
    device_options = {**entry.custom_properties}
    username = entry.username
    if username:
        device_options["username"] = username

    password = entry.password
    if password:
        device_options["password"] = password
    return device_options
