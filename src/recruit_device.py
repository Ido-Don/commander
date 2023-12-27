from main import logger
from src.device import DeviceEntry, add_device_entry, DataBase


def recruit_device(file, keepass_db_path):
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


def retrieve_device_from_input():
    return {
        "name": "12q3123",
        "username": "",
        "password": "",
        "device_options": {
            "host": "127.0.0.1",
            "port": "5002",
            "device_type": "cisco_ios"
        }
    }


def clear_device(device):
    if device:
        return True
    return False
