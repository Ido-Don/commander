import concurrent.futures
import os
from logging import Logger
from typing import List

from device_executer import execute_commands
from device import get_all_devices, KeepassDB
from global_variables import KEEPASS_DB_PATH, COMMANDER_DIRECTORY

MAX_WORKERS = 10


def deploy_commands_on_devices(commands: List[str], permission_level, logger: Logger):
    with KeepassDB(KEEPASS_DB_PATH) as kp:
        devices = get_all_devices(kp)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as execute_pool:
        future_to_name = {}
        for device in devices:
            device_options = device.device_options
            future = execute_pool.submit(execute_commands, device_options, commands, permission_level)
            future_to_name[future] = device.name

        for future in concurrent.futures.as_completed(future_to_name.keys()):
            device_name = future_to_name[future]
            try:
                results = future.result()
                handle_results(results, device_name, logger)
            except Exception as e:
                # Handle exceptions raised during the task execution
                logger.error(f"device {device_name} encountered an exception: {e}")


def handle_results(results, device_name, logger):
    outputs_folder = os.path.join(COMMANDER_DIRECTORY, 'ouputs')
    if not os.path.isdir(outputs_folder):
        os.mkdir(outputs_folder)
    device_output_txt_file = os.path.join(outputs_folder, device_name + ".txt")
    with open(device_output_txt_file, 'w+') as f:
        f.write(results)
    logger.info(f'saved results in "{device_output_txt_file}"')
