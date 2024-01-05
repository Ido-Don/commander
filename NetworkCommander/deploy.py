import concurrent.futures
import os
from typing import List

import netmiko
import typer

from NetworkCommander.__init__ import COMMANDER_DIRECTORY
from NetworkCommander.device import Device
from NetworkCommander.device_executer import execute_commands, PermissionLevel

MAX_WORKERS = 10


def deploy_commands(commands: List[str], devices: List[Device], permission_level: PermissionLevel):
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as execute_pool:
        future_to_device = {}
        for device in devices:
            device_options = device.device_options
            future = execute_pool.submit(execute_commands, device_options, commands, permission_level)
            future_to_device[future] = device

        for future in concurrent.futures.as_completed(future_to_device.keys()):
            device = future_to_device[future]
            try:
                result = future.result()
                typer.echo(f"✅  connected successfully to {device}")
                yield result, device
            except netmiko.NetmikoAuthenticationException as e:
                typer.echo(f"⛔  wasn't able to authenticate to {str(device)}", err=True)
            except netmiko.NetmikoTimeoutException as e:
                typer.echo(f"⛔  wasn't able to connect to {str(device)}", err=True)
            except Exception as e:
                # Handle exceptions raised during the task execution
                typer.echo(f"⛔  device {str(device)} encountered an exception: {e}", err=True)


def handle_results(results: str, device_name: str):
    outputs_folder = os.path.join(COMMANDER_DIRECTORY, 'outputs')
    if not os.path.isdir(outputs_folder):
        os.mkdir(outputs_folder)
    device_output_txt_file = os.path.join(outputs_folder, device_name + ".txt")
    with open(device_output_txt_file, 'w+') as f:
        f.write(results)
    typer.echo(f'✅  saved results in "{device_output_txt_file}"')
