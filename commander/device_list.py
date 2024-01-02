from typing import List

from device import Device
from keepass import KeepassDB, get_all_devices


def get_device_list(keepass_db_path: str) -> str:
    with KeepassDB(keepass_db_path) as kp:
        devices = get_all_devices(kp)

    formatted_device_list = format_device_list(devices)
    return formatted_device_list


def format_device_list(devices: List[Device]) -> str:
    output = ""
    for device in devices:
        output += str(device) + '\n'
    return output
