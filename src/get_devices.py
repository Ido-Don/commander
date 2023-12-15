from pykeepass import pykeepass

from src.global_variables import KEEPASS_DB_PATH, KEEPASS_PASSWORD


def get_all_devices():
    kp = pykeepass.PyKeePass(KEEPASS_DB_PATH, password=KEEPASS_PASSWORD)
    device_group = kp.find_groups(name="devices")[0]
    devices = {}
    for device in device_group.entries:
        device_options = get_device_options(device)
        device_title = device.title
        devices[device_title] = device_options
    return devices


def get_device_options(device: pykeepass.Entry):
    device_options = {**device.custom_properties}
    username = device.username
    if username:
        device_options["username"] = username

    password = device.password
    if password:
        device_options["password"] = password
    return device_options
