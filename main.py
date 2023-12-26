import concurrent.futures
import logging
import os
import sys
from getpass import getpass
from typing import Annotated, Optional

import typer
import yaml

from device_executer import execute_commands
from src.device import get_all_devices, DeviceEntry, add_device_entry
from src.global_variables import COMMANDER_DIRECTORY, KEEPASS_DB_PATH
from src.init import is_initialized, init_program

MAX_WORKERS = 5
logger = logging.Logger("commander")
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel("INFO")
logger.addHandler(handler)

app = typer.Typer()


def is_valid_command(command: str):
    if command:
        return True
    return False


def commands_reader(command_file_path):
    with open(command_file_path) as commands_file:
        commands = commands_file.readlines()
        commands = [command.strip("\n ") for command in commands]
        commands = filter(lambda command: is_valid_command(command), commands)
        commands = list(commands)
    return commands


def handle_results(results, device_name):
    outputs_folder = os.path.join(COMMANDER_DIRECTORY, 'ouputs')
    if not os.path.isdir(outputs_folder):
        os.mkdir(outputs_folder)
    device_output_txt_file = os.path.join(outputs_folder, device_name + ".txt")
    with open(device_output_txt_file, 'w+') as f:
        f.write(results)
    logger.info(f'saved results in "{device_output_txt_file}"')


@app.command()
def deploy(command_file: str, permission_level: str = "user"):
    execute_commands_on_devices(command_file, permission_level)


def execute_commands_on_devices(command_file_path, permission_level):
    keepass_password = getpass("enter keepass database master password: ")
    if not is_initialized(KEEPASS_DB_PATH, keepass_password):
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH, keepass_password)
    devices = get_all_devices(KEEPASS_DB_PATH, keepass_password)
    commands = commands_reader(command_file_path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as execute_pool:
        future_to_name = {}
        for device_name, device_options in devices.items():
            future = execute_pool.submit(execute_commands, device_options, commands, permission_level)
            future_to_name[future] = device_name

        for future in concurrent.futures.as_completed(future_to_name.keys()):
            device_name = future_to_name[future]
            try:
                results = future.result()
                handle_results(results, device_name)
            except Exception as e:
                # Handle exceptions raised during the task execution
                logger.error(f"device {device_name} encountered an exception: {e}")


@app.command()
def list_devices():
    keepass_password = getpass("enter keepass database master password: ")
    if not is_initialized(KEEPASS_DB_PATH, keepass_password):
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH, keepass_password)
    devices = get_all_devices(KEEPASS_DB_PATH, keepass_password)
    formatted_string = yaml.dump(devices)
    logger.info(formatted_string)


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


@app.command()
def recruit_device(file: Annotated[Optional[str], typer.Argument()] = None):
    keepass_password = getpass("enter keepass database master password: ")
    if not is_initialized(KEEPASS_DB_PATH, keepass_password):
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH, keepass_password)

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
