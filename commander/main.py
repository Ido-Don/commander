import json
import logging
import sys
from typing import Annotated, Optional, TypeAlias, List

import inquirer
import rich
import typer
from rich import print as rprint

from __init__ import COMMANDER_DIRECTORY, KEEPASS_DB_PATH
from deploy import deploy_commands
from device import Device, SUPPORTED_DEVICE_TYPES
from device_executer import PermissionLevel
from device_list import get_device_list
from init import is_initialized, init_program, delete_project_files
from keepass import KeepassDB, get_all_devices, does_device_exist, remove_device, add_device_entry
from recruit_device import retrieve_device_from_input

logger = logging.Logger("commander")
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel("INFO")
logger.addHandler(handler)

app = typer.Typer(pretty_exceptions_show_locals=False)


def is_valid_command(command: str):
    if not command:
        return False
    if command[0] == '#':
        return False
    return True


@app.command(help="deploy command to all the devices in your database")
def deploy(
        command_list: Annotated[List[str], typer.Option("--command")] = None,
        command_file: Optional[typer.FileText] = None,
        permission_level: PermissionLevel = PermissionLevel.USER
):
    check_initialization()

    if not command_list and not command_file:
        rich.print("you cant deploy to devices without any commands. use commander deploy --help for more details")
        typer.Abort()

    with KeepassDB(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)

    if not devices:
        rich.print("you don't have any devices in the database. use use commander recruit --help for more details")

    all_commands = []
    if command_file:
        striped_command_file = [command.strip("\n ") for command in command_file]
        all_commands += striped_command_file

    if command_list:
        all_commands += command_list

    valid_commands = filter(is_valid_command, all_commands)
    commands = list(valid_commands)
    rich.print("commands: \n" + '\n'.join(commands))

    numbered_devices = map(lambda index, device: f"{index}. {str(device)}", devices, range(len(devices)))
    rich.print("devices: \n" + '\n'.join(numbered_devices))
    typer.confirm(f"are you sure you want to deploy {len(commands)} commands on {len(devices)} devices?", abort=True)
    deploy_commands(commands, devices, permission_level, logger)


@app.command(name="list", help="list all the devices in your command")
def list_devices():
    check_initialization()

    device_list = get_device_list(KEEPASS_DB_PATH)
    logger.info(device_list)


@app.command(help="add a device to the list of devices")
def recruit(file: Annotated[Optional[typer.FileText], typer.Argument()] = None):
    check_initialization()
    with KeepassDB(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)
        device_names = [device.name for device in devices]
        if file:
            device = retrieve_device_from_file(device_names, file)
        else:
            device = retrieve_device_from_input(device_names)

        add_device_entry(device, kp)
        typer.echo(f"😄 added device {device.name} to database")


def check_initialization():
    if not is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        raise Exception("⛔ program is not initialized, please run commander init!")


def retrieve_device_from_file(device_names: List[str], file: typer.FileText):
    device_json = json.load(file)
    device = Device.model_validate(device_json)
    if device.name in device_names:
        raise ValueError(f"⛔ device {device.name} is already in database.")

    if device.device_type not in SUPPORTED_DEVICE_TYPES:
        raise ValueError(f"⛔ device {device.device_type} is not supported.")
    return device


@app.command(help="remove a device from list")
def remove(devices: Annotated[List[str], typer.Option("--device")] = None):
    check_initialization()
    with KeepassDB(KEEPASS_DB_PATH) as kp:
        if not devices:
            all_devices = get_all_devices(kp)
            all_device_names = [device.name for device in all_devices]
            devices = inquirer.checkbox(message="which devices do you want to remove?", choices=all_device_names)
        # find all the non-existent devices
        non_existing_devices = list(filter(lambda device: not does_device_exist(device, kp), devices))
        if non_existing_devices:
            for device_name in non_existing_devices:
                logger.error(f"device {device_name} doesn't exist so it can't be deleted")
            return
        rprint(devices)
        typer.confirm(f"are you sure you want to delete {len(devices)} devices?", abort=True)
        for device_name in devices:
            remove_device(device_name, kp)


@app.command(help="initialize the project")
def init():
    rich.print("Welcome to commander!")
    if is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        rich.print("commander is already initialized")
        reinitialize: bool = typer.confirm("do you want to delete everything and start over?")
        if reinitialize:
            rich.print(f"deleting directory: {COMMANDER_DIRECTORY}")
            delete_project_files(COMMANDER_DIRECTORY)
    if not is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        rich.print(f"creating new database in {COMMANDER_DIRECTORY}")
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH)

    rich.print("finished the initialization process, have a great day")


def main():
    app()


if __name__ == '__main__':
    main()
