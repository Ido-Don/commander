import argparse
import concurrent.futures
import logging
import os
import sys
import yaml

from device_executer import execute_commands
from src.device import get_all_devices
from src.global_variables import COMMANDER_DIRECTORY, KEEPASS_DB_PATH, KEEPASS_PASSWORD
from src.init import is_initialized, init_program

MAX_WORKERS = 5
logger = logging.Logger("commander")
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel("INFO")
logger.addHandler(handler)


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


def create_list_devices_subcommand(subparsers):
    subparsers.add_parser(
        "list_devices",
        help="deploy the commands in the commands file to devices stored in .commander"
    )


def deploy(args):
    command_file_path = args.commands_file
    permission_level = args.permission_level
    execute_commands_on_devices(command_file_path, permission_level)


def create_deploy_subcommand(subparsers):
    deploy_subcommand = subparsers.add_parser(
        "deploy",
        help="deploy the commands in the commands file to devices stored in .commander"
    )
    deploy_subcommand.add_argument(
        "commands_file",
        help="the file path for commands"
    )
    deploy_subcommand.add_argument(
        "-p",
        "--permission-level",
        help="execute the commands in permission level - 'user', 'enable' or 'configure terminal'",
        default="user",
        type=str
    )


def execute_commands_on_devices(command_file_path, permission_level):
    if not is_initialized(KEEPASS_DB_PATH, KEEPASS_PASSWORD):
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH, KEEPASS_PASSWORD)
    devices = get_all_devices(KEEPASS_DB_PATH, KEEPASS_PASSWORD)
    commands = commands_reader(command_file_path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as execute_pool:
        future_to_name = {}
        for device_name, device_options in devices.items():
            future = execute_pool.submit(execute_commands, device_options, commands, permission_level)
            future_to_name[future] = device_nameq

        for future in concurrent.futures.as_completed(future_to_name.keys()):
            device_name = future_to_name[future]
            try:
                results = future.result()
                handle_results(results, device_name)
            except Exception as e:
                # Handle exceptions raised during the task execution
                logger.error(f"device {device_name} encountered an exception: {e}")


def create_add_device_subcommand(subparsers):
    subparser = subparsers.add_parser(
        "add_device",
        help="deploy the commands in the commands file to devices stored in .commander"
    )
    subparser.add_argument(
        "-f",
        "--file",
        help="add a device from file",
        required=False
    )


def list_devices(args):
    if not is_initialized(KEEPASS_DB_PATH, KEEPASS_PASSWORD):
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH, KEEPASS_PASSWORD)
    devices = get_all_devices(KEEPASS_DB_PATH, KEEPASS_PASSWORD)
    formatted_string = yaml.dump(devices)
    logger.info(formatted_string)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="connect and manage multiple network devices",
        dest="subcommand",
        help="Available subcommands"
    )

    create_deploy_subcommand(subparsers)

    create_list_devices_subcommand(subparsers)

    create_add_device_subcommand(subparsers)
    args = parser.parse_args()
    if args.subcommand == "deploy":
        deploy(args)
    if args.subcommand == "list_devices":
        list_devices(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
