import argparse
import concurrent.futures
import json
import os
import threading
from getpass import getpass

import pykeepass

import os

from device_executer import execute_commands

HOME_FOLDER = os.path.expanduser("~")
COMMANDER_DIRECTORY = os.path.join(HOME_FOLDER, ".commander")
KEEPASS_DB_PATH = os.path.join(COMMANDER_DIRECTORY, "db.kdbx")
KEEPASS_PASSWORD = getpass("enter keepass database master password: ")


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


def list_files_in_folder(folder_path):
    files = os.scandir(folder_path)
    files = filter(lambda path: os.path.isfile(path), files)
    return files


def device_reader(device_file_path):
    with open(device_file_path) as device_file:
        device_options = json.load(device_file)
    return device_options


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


def init_program():
    os.mkdir(COMMANDER_DIRECTORY)
    create_new_keepass_db()


def create_new_keepass_db():
    kp = pykeepass.create_database(KEEPASS_DB_PATH, password=KEEPASS_PASSWORD)
    kp.save()


def get_devices():
    kp = pykeepass.PyKeePass(KEEPASS_DB_PATH, password=KEEPASS_PASSWORD)
    device_group = kp.find_groups(name="devices")[0]
    devices = {}
    for device in device_group.entries:
        device_title = device.title
        devices[device_title] = {}
        username = device.username
        if username:
            devices[device_title]["username"] = username
        password = device.password
        if password:
            devices[device_title]["password"] = password
        host = device.get_custom_property("host")
        devices[device_title]["host"] = host
        port = device.get_custom_property("port")
        if port:
            devices[device_title]["port"] = port
        device_type = device.get_custom_property("device_type")
        if device_type:
            devices[device_title]["device_type"] = device_type
    return devices


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
