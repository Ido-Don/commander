import logging
import sys
from typing import Annotated, List

import inquirer
import rich
import typer

from NetworkCommander.__init__ import COMMANDER_DIRECTORY, KEEPASS_DB_PATH
from NetworkCommander.deploy import deploy_commands, handle_results
from NetworkCommander.device_executer import PermissionLevel
from NetworkCommander.device_list import print_devices
from NetworkCommander.init import is_initialized, init_program, delete_project_files
from NetworkCommander.keepass import KeepassDB, get_all_devices, remove_device, add_device_entry
from NetworkCommander.recruit_device import retrieve_device_from_file, retrieve_device_from_input

logger = logging.Logger("commander")
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel("INFO")
logger.addHandler(handler)

app = typer.Typer(pretty_exceptions_show_locals=False)
device_group = typer.Typer(pretty_exceptions_show_locals=False,
                           help="control and manage the devices under your command")
app.add_typer(device_group, name="device")


def is_valid_command(command: str):
    if not command:
        return False
    if command[0] == '#':
        return False
    return True


@device_group.callback()
def check_initialization():
    if not is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        raise Exception("⛔ program is not initialized, please run commander init!")


@device_group.command(help="try to connect to all the devices in your database")
def ping():
    with KeepassDB(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)

    if not devices:
        raise Exception("😔 you don't have any devices in the database.")

    print_devices(devices)

    # deploy no commands just to test connectivity
    list(deploy_commands([], devices, PermissionLevel.USER))


@device_group.command(help="deploy command to all the devices in your database")
def deploy(
        command_list: Annotated[List[str], typer.Option("--command")] = None,
        command_file: typer.FileText = None,
        permission_level: PermissionLevel = PermissionLevel.USER
):
    if not command_list and not command_file:
        raise Exception("⛔ you cant deploy to devices without any commands.")

    with KeepassDB(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)

    if not devices:
        raise Exception("😔 you don't have any devices in the database.")

    all_commands = []
    if command_file:
        all_commands += command_file

    if command_list:
        all_commands += command_list

    all_commands = [command.strip("\n ") for command in all_commands]
    all_commands = list(filter(bool, all_commands))

    invalid_commands_exist = all(map(is_valid_command, all_commands))
    if not invalid_commands_exist:
        invalid_commands = filter(is_valid_command, all_commands)
        raise Exception(f"⛔ {','.join(invalid_commands)} are not valid commands.")

    rich.print("commands:")
    for command in all_commands:
        rich.print(f"{command}")

    print_devices(devices)

    typer.confirm(f"do you want to deploy these {len(all_commands)} commands on {len(devices)} devices?", abort=True)
    for result, device in deploy_commands(all_commands, devices, permission_level):
        handle_results(result, device.name)


@device_group.command(name="list", help="list all the devices in your command")
def list_devices():
    with KeepassDB(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)

    print_devices(devices)


@device_group.command(help="add a device to the list of devices")
def recruit(file: Annotated[typer.FileText, typer.Argument()] = None):
    with KeepassDB(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)
        device_names = [device.name for device in devices]
        if file:
            device = retrieve_device_from_file(device_names, file)
        else:
            device = retrieve_device_from_input(device_names)

        add_device_entry(device, kp)
        typer.echo(f"😄 added device {device.name} to database")


@device_group.command(help="remove a device from list")
def remove(devices: Annotated[List[str], typer.Option("--device")] = None):
    with KeepassDB(KEEPASS_DB_PATH) as kp:

        all_devices = get_all_devices(kp)
        all_device_names = [device.name for device in all_devices]

        if not devices:
            devices = inquirer.checkbox(message="⚠️ which devices do you want to remove?", choices=all_device_names)

        non_existing_devices = set(devices) - set(all_device_names)
        if non_existing_devices:
            raise Exception(f"⛔ devices {', '.join(non_existing_devices)} don't exist")

        print_devices(devices)
        typer.confirm(f"⚠️ are you sure you want to delete {len(devices)} devices?", abort=True)

        for device_name in devices:
            remove_device(device_name, kp)

        typer.echo(f"🗑️ deleted {len(devices)} devices")


@app.command(help="initialize the project")
def init():
    rich.print("Welcome to commander! 🥳")
    if is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        rich.print("😯 commander is already initialized")
        reinitialize = typer.confirm("⚠️ do you want to delete everything and start over?")

        if reinitialize:
            rich.print(f"🗄️ deleting directory: {COMMANDER_DIRECTORY}")
            delete_project_files(COMMANDER_DIRECTORY)

    if not is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        rich.print(f"creating new database in {COMMANDER_DIRECTORY}")
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH)

    rich.print("😁 finished the initialization process, have a great day")


def main():
    app()


if __name__ == '__main__':
    main()
