import logging
import sys
from getpass import getpass
from typing import Annotated, Optional

import typer
import yaml

from src.deploy import deploy_commands_on_devices
from src.device import get_all_devices, DeviceEntry, add_device_entry
from src.global_variables import COMMANDER_DIRECTORY, KEEPASS_DB_PATH
from src.init import is_initialized, init_program

logger = logging.Logger("commander")
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel("INFO")
logger.addHandler(handler)

app = typer.Typer()


@app.command(help="deploy command to all the devices in your database")
def deploy(command_file: str, permission_level: str = "user"):
    deploy_commands_on_devices(command_file, permission_level)


@app.command(name="list", help="list all the devices in your command")
def list_devices():
    keepass_password = getpass("enter keepass database master password: ")
    device_list = get_device_list(keepass_password, KEEPASS_DB_PATH, COMMANDER_DIRECTORY)
    logger.info(device_list)


def get_device_list(keepass_password, keepass_db_path, commander_directory):
    if not is_initialized(keepass_db_path, keepass_password):
        init_program(commander_directory, keepass_db_path, keepass_password)
    devices = get_all_devices(keepass_db_path, keepass_password)
    formatted_device_list = yaml.dump(devices)
    return formatted_device_list


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


@app.command(help="add a device to the list of devices")
def recruit(file: Annotated[Optional[str], typer.Argument()] = None):
    keepass_password = getpass("enter keepass database master password: ")
    if not is_initialized(KEEPASS_DB_PATH, keepass_password):
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH, keepass_password)

    device = None
    if file:
        device = retrieve_device_from_file(file)
    else:
        device = retrieve_device_from_input()
    if not clear_device(device):
        logger.error(f"the device {device} is not properly formatted")
        return

    device_entry = DeviceEntry(**device)

    add_device_entry(device_entry, KEEPASS_DB_PATH, keepass_password)
    logger.info("added device to database")


def main():
    app()


if __name__ == '__main__':
    main()
