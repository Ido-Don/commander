import logging
import re
import sys
from typing import Annotated, List

import rich
import typer
from rich.prompt import Prompt

from NetworkCommander.__init__ import COMMANDER_DIRECTORY, __version__
from NetworkCommander.deploy import deploy_commands, handle_results
from NetworkCommander.device import supported_device, Device, extract_ssh_connection_info
from NetworkCommander.device_executer import PermissionLevel
from NetworkCommander.device_list import print_devices
from NetworkCommander.init import is_initialized, init_program, delete_project_files
from NetworkCommander.keepass import KeepassDB, get_all_device_entries, remove_device, add_device_entry, tag_device, \
    untag_device, get_device_tags, get_device, does_device_exist

logger = logging.Logger("commander")
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel("INFO")
logger.addHandler(handler)

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


@device_command_group.callback()
def check_initialization():
    if not is_initialized(COMMANDER_DIRECTORY, KeepassDB.KEEPASS_DB_PATH):
        raise Exception("program is not initialized, please run commander init!")


@tag_command_group.command()
def add(device_tag: str, devices: List[str]):
    """
    add a tag to devices
    """
    with KeepassDB(KeepassDB.KEEPASS_DB_PATH, KeepassDB.keepass_password) as kp:
        # if someone entered a wrong device name, it can't be tagged so an error is raised
        all_devices = get_all_device_entries(kp)
        all_device_names = {device.name for device in all_devices}

        # get every device that is not in the database
        non_existent_devices = set(devices) - all_device_names
        if non_existent_devices:
            raise Exception(f"devices [{', '.join(non_existent_devices)}] doesn't exist")

        # if someone entered a device that was already tagged it can't be tagged again with the same device
        all_tagged_devices = get_all_device_entries(kp, [device_tag])
        all_tagged_devices_names = {device.name for device in all_tagged_devices}
        tagged_devices = list(filter(lambda device: device in all_tagged_devices_names, devices))
        if any(tagged_devices):
            raise Exception(f"devices [{', '.join(tagged_devices)}] are already tagged")

        for device_name in devices:
            tag_device(kp, device_tag, device_name)
        rich.print(f"added '{device_tag}' tag to {len(devices)} devices")


@tag_command_group.command(name="list")
def list_tags():
    """
    list every tag you put on devices
    """
    with KeepassDB(KeepassDB.KEEPASS_DB_PATH, KeepassDB.keepass_password) as kp:
        tags = get_device_tags(kp)
        for tag in tags:
            rich.print(tag)


@tag_command_group.command()
def remove(device_tag: str, devices: List[str]):
    """
    remove a tag from devices
    """
    with KeepassDB(KeepassDB.KEEPASS_DB_PATH, KeepassDB.keepass_password) as kp:
        all_devices = get_all_device_entries(kp)
        all_device_names = [device.name for device in all_devices]
        non_existent_devices = set(devices) - set(all_device_names)
        if non_existent_devices:
            raise Exception(f"devices {', '.join(non_existent_devices)} doesn't exist")

        for device_name in devices:
            untag_device(kp, device_tag, device_name)
        rich.print(f"removed {device_tag} from {len(devices)} devices")


@device_command_group.command()
def ping(
        tags: Annotated[
            List[str],
            typer.Argument(
                help="ping the devices that have all of these tags",
                show_default=False
            )
        ] = None
):
    """
    try to connect to the devices in your database.
    """
    with KeepassDB(KeepassDB.KEEPASS_DB_PATH, KeepassDB.keepass_password) as kp:
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
        tags: Annotated[
            List[str],
            typer.Argument(help="deploy the commands to devices matching these tags", show_default=False)
        ] = None,
        command: str = typer.Argument(... if sys.stdin.isatty() else PIPE,
                                      help="enter the command you want to deploy to your devices, you can also pipe "
                                           "them in.",
                                      show_default=False
                                      ),
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

    # if the commands come from pipe than we need to read them from stdin and filter for empty lines
    if command == PIPE:
        command = sys.stdin.read()
        commands = command.split('\n')
        commands = list(filter(bool, commands))

    # if the commands come directly from the user (through the cli argument) then we need to convert them to a list
    else:
        commands = [command]

    with KeepassDB(KeepassDB.KEEPASS_DB_PATH, KeepassDB.keepass_password) as kp:
        devices = set(get_all_device_entries(kp, tags))
        if extra_devices:

            # check for devices that don't exist
            all_devices = get_all_device_entries(kp)
            all_device_names = {device.name for device in all_devices}
            non_existent_devices = set(extra_devices) - all_device_names
            if non_existent_devices:
                raise Exception(f"devices [{', '.join(non_existent_devices)}] don't exist")
            devices.update({get_device(kp, extra_device) for extra_device in extra_devices})

    if not devices:
        raise Exception("you don't have any devices in the database.")

    invalid_commands_exist = all(map(is_valid_command, commands))
    if not invalid_commands_exist:
        invalid_commands = filter(is_valid_command, commands)
        raise Exception(f"{','.join(invalid_commands)} are not valid commands.")

    rich.print("commands:")
    for command in commands:
        rich.print(f"{command}")

    print_devices(devices)

    typer.confirm(f"do you want to deploy these {len(commands)} commands on {len(devices)} devices?", abort=True)
    for result, device in deploy_commands(commands, devices, permission_level):
        handle_results(result, device.name)


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
    with KeepassDB(KeepassDB.KEEPASS_DB_PATH, KeepassDB.keepass_password) as kp:
        devices = get_all_device_entries(kp, tags)

    print_devices(devices)


@device_command_group.command()
def add(
        name: Annotated[str, typer.Option()] = None,
        password: Annotated[str, typer.Option()] = None,
        device_type: Annotated[supported_device, typer.Option()] = "cisco_ios",
        ssh_string: Annotated[str, typer.Argument(show_default=False)] = ... if sys.stdin.isatty() else PIPE,
):
    """
    add a new device to the list of devices
    """

    # if the ssh string come from pipe than we need to read them from stdin
    if ssh_string == PIPE:
        ssh_string = sys.stdin.read()
        ssh_string = ssh_string.strip(' \n\r')

    matched_ssh_strings = re.match("[^@]*@[^@:]*:?[0-9]*", ssh_string)
    if not matched_ssh_strings:
        raise Exception(f"sorry, {ssh_string} isn't a valid ssh connection string")

    with KeepassDB(KeepassDB.KEEPASS_DB_PATH, KeepassDB.keepass_password) as kp:
        if does_device_exist(kp, name):
            raise Exception(f"device {name} already exist in keepass")

        if not password:
            password = Prompt.ask("Device password", password=True)

        match = matched_ssh_strings[0]
        username, host, port = extract_ssh_connection_info(match)

        if not name:
            name = host

        device = Device(name, username, password, host, device_type.value, port)
        add_device_entry(kp, device)
        typer.echo(f"added device {str(device)} to database")


@device_command_group.command()
def remove(devices: List[str]):
    """
    remove a device from your database
    """
    with KeepassDB(KeepassDB.KEEPASS_DB_PATH, KeepassDB.keepass_password) as kp:
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
    if is_initialized(COMMANDER_DIRECTORY, KeepassDB.KEEPASS_DB_PATH):
        rich.print("commander is already initialized")
        reinitialize = typer.confirm("do you want to delete everything and start over?")

        if reinitialize:
            rich.print(f"deleting directory: {COMMANDER_DIRECTORY}")
            delete_project_files(COMMANDER_DIRECTORY)

    if not is_initialized(COMMANDER_DIRECTORY, KeepassDB.KEEPASS_DB_PATH):
        rich.print(f"creating new database in {COMMANDER_DIRECTORY}")
        init_program(COMMANDER_DIRECTORY, KeepassDB.KEEPASS_DB_PATH)

    rich.print("finished the initialization process, have a great day")


def main():
    app()


if __name__ == '__main__':
    main()
