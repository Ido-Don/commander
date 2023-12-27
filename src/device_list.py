import yaml

from src.device import get_all_devices
from src.init import is_initialized, init_program


def get_device_list(keepass_password, keepass_db_path, commander_directory):
    if not is_initialized(keepass_db_path, keepass_password):
        init_program(commander_directory, keepass_db_path, keepass_password)
    devices = get_all_devices(keepass_db_path, keepass_password)
    formatted_device_list = yaml.dump(devices)
    return formatted_device_list
