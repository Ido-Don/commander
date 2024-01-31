import concurrent.futures
from typing import List, Iterable

import netmiko
import typer

from NetworkCommander.config import config
from NetworkCommander.device import Device
from NetworkCommander.device_executer import execute_commands, PermissionLevel


def deploy_commands(
        commands: List[str],
        devices: Iterable[Device],
        permission_level: PermissionLevel
):
    with concurrent.futures.ThreadPoolExecutor(max_workers=config["max_worker"]) as execute_pool:
        future_to_device = {}
        for device in devices:
            device_options = device.device_options
            future = execute_pool.submit(execute_commands, device_options, commands, permission_level)
            future_to_device[future] = device

        for future in concurrent.futures.as_completed(future_to_device.keys()):
            device = future_to_device[future]
            try:
                result = future.result()
                typer.echo(f"connected successfully to {device}")
                yield result, device
            except netmiko.NetmikoAuthenticationException:
                typer.echo(f"wasn't able to authenticate to {str(device)}", err=True)
            except netmiko.NetmikoTimeoutException:
                typer.echo(f"wasn't able to connect to {str(device)}", err=True)
            except Exception as e:
                # Handle exceptions raised during the task execution
                typer.echo(f"device {str(device)} encountered an exception: {e}", err=True)
