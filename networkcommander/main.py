"""
this is the main file in commander.
from here the app is created and in here all the endpoints live.
"""
import sys
from functools import reduce
from pathlib import Path
from typing import List, Optional, Iterable, Union, Annotated, Tuple, TypeVar

import netmiko
import rich
import typer
from rich.progress import Progress

from networkcommander.__init__ import __version__
from networkcommander.commander_logging import commander_logger, add_console_handler
from networkcommander.config import config, USER_CONFIG_FILE_PATH
from networkcommander.deploy import deploy_commands
from networkcommander.device import Device, convert_strings_to_devices, extract_device_names, remove_device_duplicates
from networkcommander.device_executer import PermissionLevel
from networkcommander.init import is_initialized, init_commander, delete_project_files
from networkcommander.utils import print_objects, read_file, read_from_stdin, convert_to_yaml, \
    load_user_config, create_folder_if_non_existent, password_input, write_to_folder
from networkcommander.keepass import KeepassDB, filter_entries_by_tag, filter_entries_by_tags_and_names, remove_device, \
    add_device_entry, get_all_entries, tag_entry, untag_entry, entries_to_devices, filter_entries_by_tags, filter_entries_by_titles

app = typer.Typer(pretty_exceptions_show_locals=False)

T = TypeVar('T')

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
    commander_logger.info("executing commander version.")
    typer.echo(f"Commander version: {__version__}")


@app.callback(help="")
def change_log_level(verbose: Annotated[
    Optional[bool],
    typer.Option("--verbose", "-v")
] = False
):
    """
    this callback is here to give the user the ability to print to console the logging massages.

    :param verbose: if true log everything to console, defaults to False
    """
    if not verbose:
        return
    add_console_handler(config["logging_file_level"])


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
            USER_CONFIG_FILE_PATH,
            commander_logger
    ):
        raise EnvironmentError(
            "program is not initialized, please run commander init!")
    commander_logger.debug("finished the initialization check callback")


@tag_command_group.command(name="add")
def add_tag(device_tag: str, device_names: List[str]):
    """
    add a tag to devices
    """
    device_names_to_be_tagged = set(device_names)
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp, commander_logger)
        all_devices = entries_to_devices(all_entries)
        all_device_names = extract_device_names(all_devices)

        # if someone entered a wrong device name, it can't be tagged so an error is raised
        fabricated_device_names = device_names_to_be_tagged - all_device_names
        if fabricated_device_names:
            raise LookupError(
                f"devices [{', '.join(fabricated_device_names)}] doesn't exist")

        # if someone entered a device that was already tagged it can't be tagged again

        every_tagged_entries = filter_entries_by_tag(all_entries, device_tag)
        every_tagged_devices = entries_to_devices(every_tagged_entries)
        every_tagged_device_name = extract_device_names(every_tagged_devices)

        # if there are any devices that need to be tagged and are already tagged they will be in
        # the intersection between the two groups
        tagged_device_names_that_need_to_be_tagged = device_names_to_be_tagged.intersection(
            every_tagged_device_name
        )
        if tagged_device_names_that_need_to_be_tagged:
            raise ValueError(
                "devices "
                f"[{', '.join(tagged_device_names_that_need_to_be_tagged)}] "
                "are already tagged"
            )
        entries_to_tag = filter_entries_by_titles(
            all_entries, device_names_to_be_tagged
        )

        for entry_to_tag in entries_to_tag:
            tag_entry(entry_to_tag, device_tag)
        rich.print(
            f"added '{device_tag}' tag to {len(device_names_to_be_tagged)} devices"
        )


@tag_command_group.command(name="list")
def list_tags():
    """
    list every tag you put on devices
    """
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp, commander_logger)
    entries_tags: Tuple[Union[List[str], None], ...] = tuple(
        entry.tags for entry in all_entries
    )
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
        all_entries = get_all_entries(kp, commander_logger)
        all_devices = entries_to_devices(all_entries)
        all_device_names = extract_device_names(all_devices)
        non_existent_devices = device_names_to_be_untagged - all_device_names
        if non_existent_devices:
            raise LookupError(
                f"devices {', '.join(non_existent_devices)} doesn't exist")
        entries_to_untag = filter(
            lambda entry: entry.title in device_names_to_be_untagged, all_entries)
        for entry_to_untag in entries_to_untag:
            untag_entry(entry_to_untag, device_tag)
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
        all_entries = get_all_entries(kp, commander_logger)

    if tags:
        tag_set = set(tags)
        all_tagged_entries = filter_entries_by_tags(all_entries, tag_set)
        devices = entries_to_devices(all_tagged_entries)
    else:
        devices = entries_to_devices(all_entries)

    if not devices:
        if not tags:
            raise ValueError("you don't have any devices in the database.")
        raise ValueError(
            "you don't have any devices in the database with all of these tags: "
            f"{', '.join(tags)}."
        )

    print_objects(devices, "devices")

    with Progress() as progress:
        task = progress.add_task(
            "connecting to devices...", total=len(devices))

        # deploy no commands just to test connectivity
        for _, device, exception in deploy_commands([], devices, PermissionLevel.USER):
            if exception:
                handel_exception(device, exception)
            else:
                rich.print(f"connected successfully to {str(device)}")
            progress.advance(task)


@device_command_group.command()
def deploy(
        commands: List[str] = typer.Argument(
            metavar="configuration commands",
            help="enter the commands you want to deploy to your devices",
            show_default=False
        ),
        output_folder: Path = typer.Option(None, "--output_folder", "-o"),
        tags: List[str] = typer.Option(
            list(),
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
            list(),
            "--device",
            "-d",
            help="you can specify devices you wish would run these commands on."
        ),
):
    """
    deploy command to all the devices in your database that match the tags.
    """
    create_folder_if_non_existent(output_folder)

    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp, commander_logger)

    if not all_entries:
        raise ValueError("you don't have any devices in the database.")

    tag_set = set(tags)
    extra_device_name_set = set(extra_device_names)

    every_tagged_entry_and_extra_entry = filter_entries_by_tags_and_names(
        all_entries,
        tag_set,
        extra_device_name_set
    )
    devices = entries_to_devices(every_tagged_entry_and_extra_entry)

    if not devices:
        raise ValueError("you don't have any devices in the database.")

    print_objects(devices, "devices")
    print_objects(commands, "commands")

    typer.confirm(
        f"do you want to deploy {len(commands)} "
        f"commands on {len(devices)} devices "
        f"in {permission_level} mode?",
        abort=True
    )

    with Progress() as progress:
        task = progress.add_task(
            "connecting to devices...", total=len(devices))

        for result, device, exception in deploy_commands(commands, devices, permission_level):
            handel_results(device, exception, output_folder, result)
            progress.advance(task)


def handel_exception(device: Device, exception: Exception) -> None:
    try:
        raise exception
    except KeyboardInterrupt:
        print("keyboard Interrupt")
        exit(1)
    except netmiko.NetmikoAuthenticationException:
        print(f"wasn't able to authenticate to {str(device)}", file=sys.stderr)
    except netmiko.NetmikoTimeoutException:
        print(f"wasn't able to connect to {str(device)}", file=sys.stderr)
    except Exception:  # pylint: disable=broad-exception-caught
        print(
            f"device {str(device)} encountered an exception: {str(exception)}",
            file=sys.stderr
        )


def handel_results(device, exception, output_folder, result):
    if exception:
        handel_exception(device, exception)
    else:
        rich.print(f"connected successfully to {str(device)}")
        if output_folder:
            write_to_folder(device.name, output_folder, result)
        else:
            rich.print(result)


@device_command_group.command(name="list")
def list_devices(
        tags_list: List[str] = typer.Option(
            None,
            "--tag",
            "-t",
            help="list the devices matching these tags",
            show_default=False
        )
):
    """
    list all the devices under your command.
    """
    commander_logger.info(
        "executing commander device list with these tags: %s",
        tags_list
    )
    tags_set = set(tags_list)
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp, commander_logger)

    all_tagged_entries = filter_entries_by_tags(all_entries, tags_set)
    all_tagged_devices = entries_to_devices(all_tagged_entries)

    print_objects(all_tagged_devices, "devices")


@device_command_group.command(name="add")
def add_devices(
        password: str = typer.Option(""),
        enable_password: str = typer.Option(""),
        optional_parameters_file: Optional[typer.FileText] = typer.Option(
            None, show_default=False),
        devices_file: typer.FileText = typer.Option(
            sys.stdin, show_default=False),
        ignore_pre_existing: bool = typer.Option(
            False,
            help="if set then devices that are already in keepass won't be taken "
                 "into consideration. (i.e. won't be added to keepass and won't cause an error)",
            show_default=False
        )
):
    """
    add new devices to the list of devices
    """
    # TODO: make this function smaller, brake it up.
    device_strings = []
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

    default_optional_parameters = config["optional_parameters"]
    if not default_optional_parameters:
        default_optional_parameters = {}

    optional_parameters = default_optional_parameters

    if enable_password:
        optional_parameters["secret"] = enable_password

    if optional_parameters_file:
        file_content: List[str] = read_file(optional_parameters_file)
        joined_file_content = '\n'.join(file_content)
        optional_parameters.update(convert_to_yaml(joined_file_content))

    new_devices = convert_strings_to_devices(
        device_strings, password, optional_parameters)

    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp, commander_logger)
        all_devices = entries_to_devices(all_entries)
        all_device_names = extract_device_names(all_devices)
        devices_to_add = new_devices
        if not ignore_pre_existing:
            pre_existing_devices = tuple(
                filter(
                    lambda new_device: new_device.name in all_device_names,
                    new_devices
                )
            )
            pre_existing_device_names = extract_device_names(
                pre_existing_devices)
            if any(pre_existing_device_names):
                raise LookupError(
                    "devices ["
                    f"{', '.join(pre_existing_device_names)}"
                    "] already exist in keepass"
                )
        else:
            new_non_existing_devices = tuple(filter(
                lambda new_device: new_device.name not in all_device_names,
                new_devices
            ))
            new_non_existing_unique_devices = remove_device_duplicates(
                new_non_existing_devices
            )
            devices_to_add = new_non_existing_unique_devices

        for device in devices_to_add:
            add_device_entry(kp, device)
            typer.echo(f"added device {str(device)} to database")
    typer.echo(f"added {len(devices_to_add)} devices to database")


@device_command_group.command(name="remove")
def remove_devices(device_names: List[str]):
    """
    remove a device from your database
    """
    device_names_to_be_removed = set(device_names)
    with KeepassDB(config['keepass_db_path'], config['keepass_password']) as kp:
        all_entries = get_all_entries(kp, commander_logger)
        all_devices = entries_to_devices(all_entries)
        all_device_names = extract_device_names(all_devices)

        non_existing_devices = device_names_to_be_removed - all_device_names
        if non_existing_devices:
            raise LookupError(
                f"devices {', '.join(non_existing_devices)} don't exist"
            )

        device_entries = tuple(filter(
            lambda device: device.name in device_names_to_be_removed, all_devices
        ))
        print_objects(device_entries, "devices")
        typer.confirm(
            f"are you sure you want to delete {len(device_entries)} devices?", abort=True
        )

        for device_name in device_names:
            remove_device(kp, device_name)

    typer.echo(f"deleted {len(device_entries)} devices")


@app.command()
def init():
    """
    initialize the project
    """
    commander_logger.info("executing commander init")
    rich.print("Welcome to commander!")
    if is_initialized(
            config['commander_directory'],
            config['keepass_db_path'],
            USER_CONFIG_FILE_PATH,
            commander_logger
    ):
        rich.print("commander is already initialized")
        reinitialize = typer.confirm(
            "do you want to delete everything (including config and database) and start over?")

        if reinitialize:
            delete_project_files(
                config['commander_directory'], commander_logger)

    if not is_initialized(
            config['commander_directory'],
            config['keepass_db_path'],
            USER_CONFIG_FILE_PATH,
            commander_logger
    ):
        init_commander(config, commander_logger)

    rich.print("finished the initialization process, have a great day")


if __name__ == '__main__':
    load_user_config()
    app()
