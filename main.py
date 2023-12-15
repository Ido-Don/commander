import argparse
import concurrent.futures
import json
import os
import threading
from getpass import getpass

import pykeepass

import os

from device_executer import execute_commands
from src.get_devices import get_devices
from src.global_variables import KEEPASS_PASSWORD, KEEPASS_DB_PATH, COMMANDER_DIRECTORY
from src.init import init_program, create_new_keepass_db


def get_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("commands_file",
                            help="the file path for commands, default is 'commands.txt' under the current working "
                                 "directory",
                            default="commands.txt")
    arg_parser.add_argument("-p", "--permission-level",
                            help="execute the commands in which permission level - user, enable or configure terminal",
                            default="enable", type=str)
    arguments = arg_parser.parse_args()
    command_file_path = arguments.commands_file
    permission_level = arguments.permission_level
    return command_file_path, permission_level


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
    with open(os.path.join(outputs_folder, device_name + ".txt"), 'w+') as f:
        f.write(results)
    print(f"results: ")
    print(f"{results}")


def main():
    command_file_path, permission_level = get_arguments()
    commands = commands_reader(command_file_path)
    if not os.path.isdir(COMMANDER_DIRECTORY):
        init_program()

    if not os.path.isfile(KEEPASS_DB_PATH):
        create_new_keepass_db()

    devices = get_devices()

    max_workers = 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as execute_pool:
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
                print(f"device {device_name} encountered an exception: {e}")


if __name__ == '__main__':
    main()