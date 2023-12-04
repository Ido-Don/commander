import argparse
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from device_executer import execute_script


def get_arguments():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-c", "--commands-file",
                            help="the file path for commands, default is 'commands.txt' under the current working "
                                 "directory",
                            default="commands.txt")
    arg_parser.add_argument("-o", "--output-folder",
                            help="the folder path for the commands output",
                            default=r"outputs")
    arg_parser.add_argument("-d", "--device-folder",
                            help="the folder for the connection parameters for the devices (in json format)",
                            default=r"devices")

    arg_parser.add_argument("-p", "--permission-level",
                            help="execute the commands in which permission level - user, enable or configure terminal",
                            default="enable", type=str)
    arguments = arg_parser.parse_args()
    command_file_path = arguments.commands_file
    output_folder_path = arguments.output_folder
    device_folder_path = arguments.device_folder
    permission_level = arguments.permission_level
    return command_file_path, device_folder_path, output_folder_path, permission_level


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


def main():
    command_file_path, device_folder_path, output_folder_path, permission_level = get_arguments()
    device_files = list_files_in_folder(device_folder_path)
    if not os.path.isdir(output_folder_path):
        os.mkdir(output_folder_path)

    threads = []
    for device_file_path in device_files:
        device_file = os.path.basename(device_file_path)
        output_file_path = os.path.join(output_folder_path, device_file)

        commands = commands_reader(command_file_path)
        device_options = device_reader(device_file_path)
        t = threading.Thread(target=execute_script,
                             args=(commands, device_options, output_file_path, permission_level))
        t.start()
        threads.append(t)
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    main()
