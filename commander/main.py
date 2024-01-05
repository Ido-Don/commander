import json
import logging
import sys
from typing import Annotated, Optional, List

import inquirer
import rich
import typer
from rich import print as rprint

from __init__ import COMMANDER_DIRECTORY, KEEPASS_DB_PATH
from commander.device_list import print_devices
from deploy import deploy_commands
from device import Device, SUPPORTED_DEVICE_TYPES
from device_executer import PermissionLevel
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
        raise Exception("⛔ you cant deploy to devices without any commands.")

    with KeepassDB(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)

    if not devices:
        raise Exception("😔 you don't have any devices in the database.")

    all_commands = []
    if command_file:
        striped_command_file = [command.strip("\n ") for command in command_file]
        all_commands += striped_command_file

    if command_list:
        all_commands += command_list
    invalid_commands_exist = all(map(is_valid_command, all_commands))
    if not invalid_commands_exist:
        invalid_commands = filter(is_valid_command, all_commands)
        raise Exception(f"⛔ {','.join(invalid_commands)} are not valid commands.")

    rich.print("commands:")
    for command in all_commands:
        rich.print(f"{command}")

    print_devices(devices)

    typer.confirm(f"do you want to deploy these {len(all_commands)} commands on {len(devices)} devices?", abort=True)
    deploy_commands(all_commands, devices, permission_level, logger)


@app.command(name="list", help="list all the devices in your command")
def list_devices():
    check_initialization()

    with KeepassDB(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)

    print_devices(devices)


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
            devices = inquirer.checkbox(message="⚠️ which devices do you want to remove?", choices=all_device_names)
        # find all the non-existent devices
        non_existing_devices = list(filter(lambda device: not does_device_exist(device, kp), devices))
        if non_existing_devices:
            is_plural = len(non_existing_devices) > 1
            raise Exception(f"⛔  {'devices' if is_plural else 'device'} {', '.join(non_existing_devices)} don't exist")
        rprint(devices)
        typer.confirm(f"⚠️ are you sure you want to delete {len(devices)} devices?", abort=True)
        for device_name in devices:
            remove_device(device_name, kp)
        typer.echo(f"🗑️ deleted {len(devices)} devices")


@app.command(help="initialize the project")
def init():
    rich.print("Welcome to commander! 🥳")
    if is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        rich.print("😯 commander is already initialized")
        reinitialize: bool = typer.confirm("⚠️ do you want to delete everything and start over?")
        if reinitialize:
            rich.print(f"📁 deleting directory: {COMMANDER_DIRECTORY}")
            delete_project_files(COMMANDER_DIRECTORY)
    if not is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        rich.print(f"creating new database in {COMMANDER_DIRECTORY}")
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH)

    rich.print("😁 finished the initialization process, have a great day")


def main():
    app()


if __name__ == '__main__':
    main()
