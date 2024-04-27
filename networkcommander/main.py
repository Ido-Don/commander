import json
import os.path
import sys
from functools import reduce
from itertools import filterfalse
from pathlib import Path
from typing import List, Optional, Iterable, Union, Set, Any

import netmiko
import rich
import typer
import yaml
from rich.progress import Progress

from networkcommander.__init__ import __version__
from networkcommander.config import config, USER_CONFIG_FILE
from networkcommander.deploy import deploy_commands
from networkcommander.device import device_from_string, Device
from networkcommander.device_executer import PermissionLevel
from networkcommander.init import is_initialized, init_program, delete_project_files
from networkcommander.io_utils import print_objects, read_file, read_from_stdin
from networkcommander.keepass import KeepassDB, get_all_device_entries, remove_device, \
    add_device_entry, get_device, \
    get_non_existing_device_names, get_existing_devices, does_device_exist, get_all_entries, entry_to_device, \
    tag_entry, untag_entry, is_entry_tagged, is_entry_tagged_by_multiple_tags

app = typer.Typer(pretty_exceptions_show_locals=False)

device_command_group = typer.Typer(
    pretty_exceptions_show_locals=False,
    help="control and manage the devices under your command"
)

app.add_typer(device_command_group, name="device")

tag_command_group = typer.Typer(
    pretty_exceptions_show_locals=False,
    help="tag devices to better segment them"
)

device_command_group.add_typer(tag_command_group, name="tag")


@app.command()
def version():
    """
        show the version of the application
    """
    typer.echo(f"Commander version: {__version__}")


def is_valid_command(command: str) -> bool:
    """
    checks if a string is a valid command or not
    """
    if not command:
        return False
    if command[0] == '#':
        return False
    return True


# the help="" is here so that the docstring is not shown to the user.
@app.callback(no_args_is_help=True, help="")
def load_config():
    """
    Load configuration settings from the user-specific configuration file.
    and update the application's configuration accordingly that lives in the config variable.

    Note: The configuration file is expected to be in JSON format.
    """
    if os.path.isfile(USER_CONFIG_FILE):
        with open(USER_CONFIG_FILE, encoding="UTF-8") as json_file:
            file_content = json_file.read()
            if not file_content:
                return
            user_custom_config = json.loads(file_content)
            config.update(user_custom_config)


@device_command_group.callback(no_args_is_help=True)
def initialization_check(keepass_password: Optional[str] = typer.Option(None)):
    """
    Check if Commander has been initialized with the necessary directory and user configuration.

    :param keepass_password: The password to access the Keepass database.
    :raises: an `EnvironmentError` with a message prompting the user to run `commander init`.
    """
    config['keepass_password'] = keepass_password
    if not is_initialized(
            config['commander_directory'],
            config['keepass_db_path'],
            USER_CONFIG_FILE
    ):
        raise EnvironmentError("program is not initialized, please run commander init!")


def find_value_in_set(value_bank: Set[Any]):
    def inner(value: Any):
        return value in value_bank

    return inner


@tag_command_group.command(name="add")
def add_tag(device_tag: str, device_names: List[str]):
    """
    add a tag to devices
    """
    device_names_to_be_tagged = set(device_names)
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp)
        all_devices = tuple((entry_to_device(entry) for entry in all_entries))
        all_device_names = {device.name for device in all_devices}

        # if someone entered a wrong device name, it can't be tagged so an error is raised
        fabricated_device_names = device_names_to_be_tagged - all_device_names
        if fabricated_device_names:
            raise LookupError(f"devices [{', '.join(fabricated_device_names)}] doesn't exist")

        # if someone entered a device that was already tagged it can't be tagged again

        every_tagged_entries = filter(is_entry_tagged(device_tag), all_entries)
        every_tagged_devices = tuple((entry_to_device(entry) for entry in every_tagged_entries))
        every_tagged_device_name = {device.name for device in every_tagged_devices}

        # if there are any devices that need to be tagged and are already tagged they will be in
        # the intersection between the two groups
        device_names_already_tagged_that_need_to_be_tagged = device_names_to_be_tagged.intersection(
            every_tagged_device_name
        )
        if device_names_already_tagged_that_need_to_be_tagged:
            raise ValueError(
                f"devices [{', '.join(device_names_already_tagged_that_need_to_be_tagged)}] are already tagged"
            )
        entries_to_tag = filter(lambda entry: entry.title in device_names_to_be_tagged, all_entries)
        for entry in entries_to_tag:
            tag_entry(entry, device_tag)
        rich.print(f"added '{device_tag}' tag to {len(device_names_to_be_tagged)} devices")


@tag_command_group.command(name="list")
def list_tags():
    """
    list every tag you put on devices
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp)
        entries_tags: List[Union[List[str], None]] = [entry.tags for entry in all_entries]
        entries_tags_without_none: Iterable[List[str]] = filter(None, entries_tags)
        flatten_tag_list: Iterable[str] = reduce(
            lambda aggregate, tags: aggregate + tags,
            entries_tags_without_none,
            []
        )
        unique_tags = set(flatten_tag_list)
        print_objects(unique_tags, "tags")


@tag_command_group.command(name="remove")
def remove_tag(device_tag: str, device_names: List[str]):
    """
    remove a tag from devices
    """
    device_names_to_be_untagged = set(device_names)
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp)
        all_devices = tuple((entry_to_device(entry) for entry in all_entries))
        all_device_names = {device.name for device in all_devices}
        non_existent_devices = device_names_to_be_untagged - all_device_names
        if non_existent_devices:
            raise LookupError(f"devices {', '.join(non_existent_devices)} doesn't exist")
        entries_to_untag = filter(lambda entry: entry.title in device_names_to_be_untagged, all_entries)
        for entry in entries_to_untag:
            untag_entry(entry, device_tag)
        rich.print(f"removed {device_tag} from {len(device_names)} devices")


@device_command_group.command()
def ping(
        tags: List[str] = typer.Option(
            None,
            "--tag",
            "-t",
            help="ping the devices matching these tags",
            show_default=False
        )
):
    """
    try to connect to the devices in your database.
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        devices = get_all_device_entries(kp, set(tags))

    if not devices:
        if not tags:
            raise ValueError("you don't have any devices in the database.")
        raise ValueError(
            "you don't have any devices in the database with all of these tags: "
            f"{', '.join(tags)}."
        )

    print_objects(devices, "devices")

    with Progress() as progress:
        task = progress.add_task("connecting to devices...", total=len(devices))

        # deploy no commands just to test connectivity
        for result, device, exception in deploy_commands([], devices, PermissionLevel.USER):
            if exception:
                try:
                    raise exception
                except netmiko.NetmikoAuthenticationException:
                    print(f"wasn't able to authenticate to {str(device)}", file=sys.stderr)
                except netmiko.NetmikoTimeoutException:
                    print(f"wasn't able to connect to {str(device)}", file=sys.stderr)
                except Exception as exception:
                    print(f"device {str(device)} encountered an exception: {exception}", file=sys.stderr)
            else:
                rich.print(f"connected successfully to {str(device)}")
            progress.advance(task)


@device_command_group.command()
def deploy(
        commands: Optional[List[str]] = typer.Argument(
            None,
            metavar="configuration commands",
            help="enter the commands you want to deploy to your devices",
            show_default=False
        ),
        output_folder: Path = typer.Option(None, "--output_folder", "-o"),
        tags: List[str] = typer.Option(
            None,
            "--tag",
            "-t",
            help="deploy the commands to devices matching these tags",
            show_default=False
        ),
        permission_level: PermissionLevel = typer.Option(
            'user',
            "--permission_level",
            "-p",
            help="the permission level the commands will run at"
        ),
        extra_device_names: List[str] = typer.Option(
            None,
            "--device",
            "-d",
            help="you can specify devices you wish would run these commands on."
        ),
):
    """
    deploy command to all the devices in your database that match the tags.
    """
    create_folder_if_non_existent(output_folder)

    commands = sanitize_commands(commands)

    devices = sanitize_devices(extra_device_names, tags)

    print_objects(devices, "devices")
    print_objects(commands, "commands")

    typer.confirm(
        f"do you want to deploy these {len(commands)} commands on {len(devices)} devices?",
        abort=True
    )

    with Progress() as progress:
        task = progress.add_task("connecting to devices...", total=len(devices))

        for result, device, exception in deploy_commands(commands, devices, permission_level):
            handel_results(device, exception, output_folder, result)
            progress.advance(task)


def sanitize_commands(commands):
    if not commands:
        commands = read_from_stdin()
    check_for_invalid_commands(commands)
    return commands


def handel_exception(device, exception):
    try:
        raise exception
    except netmiko.NetmikoAuthenticationException:
        print(f"wasn't able to authenticate to {str(device)}", file=sys.stderr)
    except netmiko.NetmikoTimeoutException:
        print(f"wasn't able to connect to {str(device)}", file=sys.stderr)
    except Exception as exception:
        print(f"device {str(device)} encountered an exception: {exception}", file=sys.stderr)


def handel_results(device, exception, output_folder, result):
    if exception:
        handel_exception(device, exception)
    else:
        rich.print(f"connected successfully to {str(device)}")
        if output_folder:
            write_to_folder(device.name, output_folder, result)
        else:
            rich.print(result)


def check_for_invalid_commands(commands):
    invalid_commands = list(filterfalse(is_valid_command, commands))
    if invalid_commands:
        raise ValueError(f"{','.join(invalid_commands)} are not valid commands.")


def write_to_folder(file_name, output_folder, result):
    output_file_path = output_folder.joinpath(f"{file_name}.txt")
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(result)
        rich.print(f"'saved output to {str(output_file_path)}'")


def sanitize_devices(extra_device_names, tags):
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        devices = get_all_device_entries(kp, set(tags))

        if extra_device_names:
            extra_devices = get_device_list1(kp, extra_device_names)
            for extra_device in extra_devices:
                if extra_device not in devices:
                    devices.append(extra_device)
    if not devices:
        raise ValueError("you don't have any devices in the database.")
    return devices


def get_device_list(kp, extra_device_names):
    non_existent_devices = get_non_existing_device_names(kp, extra_device_names)
    if any(non_existent_devices):
        raise ValueError(f"devices [{', '.join(non_existent_devices)}] don't exist")

    devices = [get_device(kp, extra_device) for extra_device in extra_device_names]
    return devices


def get_device_list1(kp, extra_device_names):
    non_existent_devices = get_non_existing_device_names(kp, extra_device_names)
    if any(non_existent_devices):
        raise ValueError(f"devices [{', '.join(non_existent_devices)}] don't exist")

    devices = [get_device(kp, extra_device) for extra_device in extra_device_names]
    return devices


def create_folder_if_non_existent(output_folder):
    if output_folder:
        if output_folder.exists() and not output_folder.is_dir():
            raise NotADirectoryError(f"{str(output_folder)} exist and is not a directory")
        if not output_folder.exists():
            os.mkdir(output_folder)


@device_command_group.command(name="list")
def list_devices(
        tags_list: List[str] = typer.Option(
            None,
            "--tag",
            "-t",
            help="list the devices matching these tags",
            show_default=False
        ),
):
    """
    list all the devices under your command.
    """
    tags_set = set(tags_list)
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp)

    all_tagged_entries = tuple(filter(is_entry_tagged_by_multiple_tags(tags_set),all_entries))
    all_tagged_devices = tuple((entry_to_device(entry) for entry in all_tagged_entries))

    print_objects(all_tagged_devices, "devices")


def get_non_existing_device(kp, devices):
    """
    Retrieve existing devices from the list of devices in the KeePass database.

    :param kp: The connection to the KeePass database.
    :param devices: A list of Device objects.
    :Returns: A list of Device objects representing the devices that already exist in the database.
    """
    non_existing_devices = []
    for device in devices:
        if not does_device_exist(kp, device.name):
            non_existing_devices.append(device)
    return non_existing_devices


def convert_parameters(content: List[str]):
    new_parameters = yaml.safe_load('\n'.join(content))
    return new_parameters


@device_command_group.command()
def add(
        password: str = typer.Option(""),
        enable_password: str = typer.Option(""),
        device_strings: List[str] = typer.Argument(None, show_default=False),
        optional_parameters_stream: typer.FileText = typer.Option(sys.stdin, show_default=False),
        devices_file: typer.FileText = typer.Option(sys.stdin, show_default=False),
        ignore_pre_existing: bool = typer.Option(
            False,
            help="if set then devices that are already in keepass won't be taken "
                 "into consideration. (i.e. won't be added to keepass and won't cause an error)",
            show_default=False
        )
):
    """
    add a new devices to the list of devices
    """
    if not device_strings:
        if devices_file == sys.stdin:
            rich.print("please enter the devices you want to connect to.")
            device_strings = read_from_stdin()
        elif devices_file:
            device_strings = read_file(devices_file)

    if not device_strings:
        raise ValueError("no devices entered... not adding anything")

    if not password:
        password = password_input("device's password")

    if not enable_password:
        enable_password = password_input("device's enable password")

    optional_parameters = config["optional_parameters"]

    if enable_password:
        optional_parameters["secret"] = enable_password

    if optional_parameters_stream == sys.stdin:
        rich.print("please enter any other optional parameters.")
        rich.print("specify values in YAML format, for exemple: global_delay_factor: 1.5")
        stream_content: List[str] = read_from_stdin()
        optional_parameters = convert_parameters(stream_content)
    elif optional_parameters_stream:
        stream_content: List[str] = read_file(optional_parameters_stream)
        optional_parameters = convert_parameters(stream_content)

    devices = convert_devices(device_strings, password, optional_parameters)

    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        if not ignore_pre_existing:
            check_pre_existing_devices(kp, devices)
        else:
            devices = get_non_existing_device(kp, devices)
            if not devices:
                raise ValueError("no new devices entered... not adding anything")

        add_devices(kp, devices)
    typer.echo(f"added {len(devices)} to database")


def check_pre_existing_devices(kp, devices):
    existing_devices = get_existing_devices(kp, devices)
    existing_device_names = [device.name for device in existing_devices]
    if existing_devices:
        raise LookupError(
            "devices ["
            f"{', '.join(existing_device_names)}"
            "] already exist in keepass"
        )


def add_devices(kp, devices):
    for device in devices:
        add_device_entry(kp, device)
        typer.echo(f"added device {str(device)} to database")


def convert_devices(devices: Iterable[str], password, optional_parameters) -> List[Device]:
    new_devices = [convert_device(device, password, optional_parameters) for device in devices]
    return new_devices


def convert_device(device: str, password, optional_parameters=None):
    new_device = device_from_string(device, password, optional_parameters)
    return new_device


def password_input(prompt):
    password = typer.prompt(
        prompt,
        hide_input=True,
        default="",
        show_default=False
    )
    return password


@device_command_group.command()
def remove(device_names: List[str]):
    """
    remove a device from your database
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_device_entry = get_all_device_entries(kp)
        all_device_names = [device.name for device in all_device_entry]
        non_existing_devices = set(device_names) - set(all_device_names)
        if non_existing_devices:
            raise LookupError(f"devices {', '.join(non_existing_devices)} don't exist")
        device_entries = []
        device_name_map = dict(zip(all_device_names, all_device_entry))
        for device_name in device_names:
            if device_name in device_name_map:
                device_entries.append(device_name_map[device_name])
        print_objects(device_entries, "devices")
        typer.confirm(f"are you sure you want to delete {len(device_entries)} devices?", abort=True)

        for device_name in device_names:
            remove_device(kp, device_name)

        typer.echo(f"deleted {len(device_entries)} devices")


@app.command()
def init():
    """
    initialize the project
    """
    rich.print("Welcome to commander!")
    if is_initialized(
            config['commander_directory'],
            config['keepass_db_path'],
            USER_CONFIG_FILE
    ):
        rich.print("commander is already initialized")
        reinitialize = typer.confirm("do you want to delete everything (including config and database) and start over?")

        if reinitialize:
            delete_project_files(config['commander_directory'])

    if not is_initialized(
            config['commander_directory'],
            config['keepass_db_path'],
            USER_CONFIG_FILE
    ):
        rich.print(f"creating a new database in {config['commander_directory']}")
        init_program(config['commander_directory'], config['keepass_db_path'], USER_CONFIG_FILE, config)

    rich.print("finished the initialization process, have a great day")


if __name__ == '__main__':
    app()
