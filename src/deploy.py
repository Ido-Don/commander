import concurrent.futures
import os

from device_executer import execute_commands
from main import logger
from src.device import get_all_devices, DataBase
from src.global_variables import KEEPASS_DB_PATH, COMMANDER_DIRECTORY
from src.init import is_initialized

MAX_WORKERS = 10


def deploy_commands_on_devices(command_file_path, permission_level):
    if not is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        logger.error("program is not initialized! please run commander init!")
        return

    with DataBase(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)

    commands = commands_reader(command_file_path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as execute_pool:
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
                logger.error(f"device {device_name} encountered an exception: {e}")


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


def is_valid_command(command: str):
    if command:
        return True
    return False
