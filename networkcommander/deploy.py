import concurrent.futures
import sys
from typing import List, Iterable

import netmiko
import rich
import typer

from networkcommander.config import config
from networkcommander.device import Device
from networkcommander.device_executer import execute_commands, PermissionLevel


def deploy_commands(
        commands: List[str],
        devices: Iterable[Device],
        permission_level: PermissionLevel
):
    """
    deploy a list of commands to a list of devices
    simultaneously at a designated permission level.

    :param commands: List of commands to execute.
    :param devices: a collection of devices to push the commands to.
    :param permission_level: PermissionLevel enum representing the desired permission level.
    :return: a generator that yields each result and device as they finish.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=config["max_worker"]) as execute_pool:
        future_to_device = {}

        # start the threads
        for device in devices:
            device_options = device.device_options
            function_arguments = (device_options, commands, permission_level)
            future = execute_pool.submit(execute_commands, *function_arguments)
            future_to_device[future] = device

        # wait for the threads to finish one by one.
        for future in concurrent.futures.as_completed(future_to_device.keys()):
            device = future_to_device[future]

            try:
                result = future.result()
                yield result, device, None
            except Exception as exception:
                yield "", device, exception
