import json
import os.path
import sys
from itertools import filterfalse
from pathlib import Path
from typing import Annotated, List

import rich
import typer

from NetworkCommander.__init__ import __version__
from NetworkCommander.config import config, USER_CONFIG_FILE
from NetworkCommander.deploy import deploy_commands
from NetworkCommander.device import Device
from NetworkCommander.device_executer import PermissionLevel
from NetworkCommander.device_list import print_devices
from NetworkCommander.init import is_initialized, init_program, delete_project_files
from NetworkCommander.keepass import KeepassDB, get_all_device_entries, remove_device, add_device_entry, tag_device, \
    untag_device, get_device_tags, get_device, does_device_exist, get_existing_devices, filter_non_existing_device_names

app = typer.Typer(pretty_exceptions_show_locals=False)
device_command_group = typer.Typer(pretty_exceptions_show_locals=False,
                                   help="control and manage the devices under your command")
app.add_typer(device_command_group, name="device")
tag_command_group = typer.Typer(pretty_exceptions_show_locals=False,
                                help="tag devices to better segment them")
device_command_group.add_typer(tag_command_group, name="tag")

PIPE = "PIPE_FROM_STDIN"


@app.command()
def version():
    """
        show the version of the application
    """
    typer.echo(f"Commander version: {__version__}")


def is_valid_command(command: str):
    if not command:
        return False
    if command[0] == '#':
        return False
    return True


@app.callback(no_args_is_help=True)
def load_config():
    if os.path.isfile(USER_CONFIG_FILE):
        with open(USER_CONFIG_FILE) as json_file:
            config.update(json.load(json_file))
    if 'commander_directory' not in config:
        HOME_DIRECTORY = os.path.expanduser('~')
        config['commander_directory'] = os.path.join(HOME_DIRECTORY, '.commander')
    if 'commander_directory' in config:
        config['keepass_db_path'] = os.path.join(config['commander_directory'], "db.kdbx")
    if 'default_device_type' not in config:
        config['default_device_type'] = "cisco_ios"


@device_command_group.callback(no_args_is_help=True)
def initialization_check(keepass_password: Annotated[str, typer.Option()] = None):
    config['keepass_password'] = keepass_password
    if not is_initialized(config['commander_directory'], config['keepass_db_path']):
        raise Exception("program is not initialized, please run commander init!")


@tag_command_group.command()
def add(device_tag: str, devices: List[str]):
    """
    add a tag to devices
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        # if someone entered a wrong device name, it can't be tagged so an error is raised
        non_existent_devices = filter_non_existing_device_names(kp, devices)
        if non_existent_devices:
            raise Exception(f"devices [{', '.join(non_existent_devices)}] doesn't exist")

        # if someone entered a device that was already tagged it can't be tagged again with the same device
        all_tagged_devices = get_all_device_entries(kp, [device_tag])
        all_tagged_devices_names = {device.name for device in all_tagged_devices}
        tagged_existing_devices = list(filter(lambda device: device in all_tagged_devices_names, devices))
        if any(tagged_existing_devices):
            raise Exception(f"devices [{', '.join(tagged_existing_devices)}] are already tagged")

        for device_name in devices:
            tag_device(kp, device_tag, device_name)
        rich.print(f"added '{device_tag}' tag to {len(devices)} devices")


@tag_command_group.command(name="list")
def list_tags():
    """
    list every tag you put on devices
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        tags = get_device_tags(kp)
        for tag in tags:
            rich.print(tag)


@tag_command_group.command()
def remove(device_tag: str, devices: List[str]):
    """
    remove a tag from devices
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        non_existent_devices = filter_non_existing_device_names(kp, devices)
        if non_existent_devices:
            raise Exception(f"devices {', '.join(non_existent_devices)} doesn't exist")

        for device_name in devices:
            untag_device(kp, device_tag, device_name)
        rich.print(f"removed {device_tag} from {len(devices)} devices")


@device_command_group.command()
def ping(
        tags: Annotated[
            List[str],
            typer.Option(
                help="ping the devices that have all of these tags",
                show_default=False
            )
        ] = None
):
    """
    try to connect to the devices in your database.
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        devices = get_all_device_entries(kp, tags)

    if not devices:
        if not tags:
            raise Exception("you don't have any devices in the database.")
        else:
            raise Exception(f"you don't have any devices in the database with all of these tags: {', '.join(tags)}.")

    print_devices(devices)

    # deploy no commands just to test connectivity
    list(deploy_commands([], devices, PermissionLevel.USER))


@device_command_group.command()
def deploy(
        commands: Annotated[
            List[str],
            typer.Argument(help="enter the commands you want to deploy to your devices", show_default=False)
        ] = None,
        output_folder: Annotated[Path, typer.Option("--output_folder", "-o")] = None,
        tags: Annotated[
            List[str],
            typer.Option(
                "--tag",
                "-t",
                help="deploy the commands to devices matching these tags",
                show_default=False
            )
        ] = None,
        permission_level: Annotated[PermissionLevel, typer.Option(
            "--permission_level",
            "-p",
            help="the permission level the commands will run at"
        )] = 'user',
        extra_devices: Annotated[List[str], typer.Option(
            "--device",
            "-d",
            help="you can specify devices you wish would run these commands on."
        )] = None,
):
    """
    deploy command to all the devices in your database that match the tags.
    """
    if output_folder:
        if output_folder.exists() and not output_folder.is_dir():
            raise FileExistsError(f"{str(output_folder)} is a file not a directory")
        if not output_folder.exists():
            os.mkdir(output_folder)
    if not commands:
        typer.echo("enter the commands you want to deploy and then press Control-d or Control-Z")
        commands = sys.stdin.readlines()
        commands = [command.strip(' \n').replace('\4', '').replace('\26', '') for command in commands]
        commands = list(filter(bool, commands))

    invalid_commands = list(filterfalse(is_valid_command, commands))
    if invalid_commands:
        raise Exception(f"{','.join(invalid_commands)} are not valid commands.")

    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        devices = set(get_all_device_entries(kp, tags))
        if extra_devices:

            non_existent_devices = filter_non_existing_device_names(kp, extra_devices)
            if non_existent_devices:
                raise Exception(f"devices [{', '.join(non_existent_devices)}] don't exist")

            devices.update({get_device(kp, extra_device) for extra_device in extra_devices})

    if not devices:
        raise Exception("you don't have any devices in the database.")

    print_devices(devices)
    print_commands(commands)

    typer.confirm(f"do you want to deploy these {len(commands)} commands on {len(devices)} devices?", abort=True)
    for result, device in deploy_commands(commands, devices, permission_level):
        if not output_folder:
            typer.echo(result)
        else:
            output_file_path = output_folder.joinpath(f"{device.name}.txt")
            with open(output_file_path, "w") as output_file:
                output_file.write(result)
                typer.echo(f"'saved output to {str(output_file_path.absolute().resolve())}'")


def print_commands(commands):
    rich.print("commands:")
    for commands in commands:
        rich.print(f"{commands}")


@device_command_group.command(name="list")
def list_devices(
        tags: Annotated[
            List[str],
            typer.Argument(help="list the devices matching these tags.", show_default=False)
        ] = None
):
    """
    list all the devices under your command.
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        devices = get_all_device_entries(kp, tags)

    print_devices(devices)


@device_command_group.command(name="import")
def import_devices(
        devices_file: Annotated[typer.FileText, typer.Argument(show_default=False)] = sys.stdin,
        device_password: Annotated[
            str,
            typer.Option(prompt="Devices password", hide_input=True)
        ] = ""
):
    device_strings = [device_string.strip(' \n\r') for device_string in devices_file.readlines()]
    devices = [Device.from_string(device_string) for device_string in device_strings]
    for device in devices:
        device.password = device_password
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        existing_devices = get_existing_devices(kp, devices)
        if existing_devices:
            raise Exception(f"[{', '.join(device.name for device in existing_devices)}] already exist in database, "
                            f"you can't add them again")
        for device in devices:
            typer.echo(f"adding {device} to database")
            add_device_entry(kp, device)
        typer.echo(f"added {len(devices)} to database")


@device_command_group.command()
def add(
        device_string: Annotated[str, typer.Argument(show_default=False)],
        password: Annotated[str, typer.Option(prompt="Device's password", hide_input=True)] = "",
):
    """
    add a new device to the list of devices
    """
    if not device_string:
        raise Exception("sorry you can't upload an empty connection string")
    device = Device.from_string(device_string)
    device.password = password
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        if does_device_exist(kp, device.name):
            raise Exception(f"device {device.name} already exist in keepass")

        add_device_entry(kp, device)
        typer.echo(f"added device {device} to database")


@device_command_group.command()
def remove(devices: List[str]):
    """
    remove a device from your database
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_device_entry = get_all_device_entries(kp)
        all_device_names = [device.name for device in all_device_entry]
        non_existing_devices = set(devices) - set(all_device_names)
        if non_existing_devices:
            raise Exception(f"devices {', '.join(non_existing_devices)} don't exist")
        device_entries = []
        device_name_map = dict(zip(all_device_names, all_device_entry))
        for device_name in devices:
            if device_name in device_name_map:
                device_entries.append(device_name_map[device_name])
        print_devices(device_entries)
        typer.confirm(f"are you sure you want to delete {len(device_entries)} devices?", abort=True)

        for device_name in devices:
            remove_device(kp, device_name)

        typer.echo(f"deleted {len(device_entries)} devices")


@app.command()
def init():
    """
    initialize the project
    """
    rich.print("Welcome to commander!")
    if is_initialized(config['commander_directory'], config['keepass_db_path'], USER_CONFIG_FILE):
        rich.print("commander is already initialized")
        reinitialize = typer.confirm("do you want to delete everything and start over?")

        if reinitialize:
            rich.print(f"deleting directory: {config['commander_directory']}")
            delete_project_files(config['commander_directory'])
    if not is_initialized(config['commander_directory'], config['keepass_db_path'], USER_CONFIG_FILE):
        rich.print(f"creating new database in {config['commander_directory']}")
        init_program(config['commander_directory'], config['keepass_db_path'], USER_CONFIG_FILE)

    rich.print("finished the initialization process, have a great day")


def main():
    app()


if __name__ == '__main__':
    main()
