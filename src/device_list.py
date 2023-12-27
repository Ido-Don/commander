import yaml

from src.device import get_all_devices, DataBase


def get_device_list(keepass_db_path: str) -> str:
    with DataBase(keepass_db_path) as kp:
        devices = get_all_devices(kp)
    formatted_device_list = yaml.dump(devices)
    return formatted_device_list
