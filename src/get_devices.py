from pykeepass import pykeepass

from src.global_variables import KEEPASS_DB_PATH, KEEPASS_PASSWORD


def get_all_devices():
    kp = pykeepass.PyKeePass(KEEPASS_DB_PATH, password=KEEPASS_PASSWORD)
    device_group = kp.find_groups(name="devices")[0]
    devices = {}
    for device in device_group.entries:
        device_title = device.title
        devices[device_title] = {}
        username = device.username
        if username:
            devices[device_title]["username"] = username
        password = device.password
        if password:
            devices[device_title]["password"] = password
        host = device.get_custom_property("host")
        devices[device_title]["host"] = host
        port = device.get_custom_property("port")
        if port:
            devices[device_title]["port"] = port
        device_type = device.get_custom_property("device_type")
        if device_type:
            devices[device_title]["device_type"] = device_type
    return devices
