from logging import Logger

from rich.prompt import Prompt

from src.device import DeviceEntry, add_device_entry, DataBase


def recruit_device(file, keepass_db_path, logger: Logger):
    device, error = get_device(file)

    if error:
        logger.error(str(error))
        return

    device_entry = DeviceEntry(**device)
    with DataBase(keepass_db_path) as kp:
        add_device_entry(device_entry, kp)

    logger.info(f"added device {device_entry.name}to database")


def get_device(file):
    if file:
        device = retrieve_device_from_file(file)
    else:
        device = retrieve_device_from_input()
    if not clear_device(device):
        return None, Exception(f"the device {device} is not properly formatted")
    return device, None


def retrieve_device_from_file(file):
    return retrieve_device_from_input()


SUPPORTED_DEVICES = [
    "cisco_ios",
    "cisco_ios_xe",
    "cisco_ios_telnet",
    "cisco_ios_xe_telnet"
]


def retrieve_device_from_input():
    name = Prompt.ask("Device's name")
    username = Prompt.ask("Device's username", )
    password = Prompt.ask("Device's password", password=True, default="123")
    host = Prompt.ask("Device's ip/hostname")
    device_type = Prompt.ask("Device's software Type", choices=SUPPORTED_DEVICES, default=SUPPORTED_DEVICES[0])
    default_port = "22"
    if 'telnet' in device_type:
        default_port = "23"
    port = Prompt.ask("Device's port", default=default_port, show_default=True)
    device = {
        "name": name,
        "username": username,
        "password": password,
        "device_options": {
            "host": host,
            "port": port,
            "device_type": device_type
        }
    }
    return device


def clear_device(device):
    if device:
        return True
    return False
