from enum import Enum
from typing import List

import netmiko


class PermissionLevel(str, Enum):
    """
    Enum defining permission levels for network device command.
    """
    USER = "user"
    ENABLE = "enable"
    CONFIGURE_TERMINAL = "configure_terminal"


def change_permission(device: netmiko.BaseConnection, permission_level: PermissionLevel):
    """
    Change the permission level of the network device.

    :param device: Netmiko connection object.
    :param permission_level: PermissionLevel enum representing the desired permission level.
    """
    is_in_config_mode = device.check_config_mode()
    is_in_enable_mode = device.check_enable_mode()
    if permission_level == "enable":
        if is_in_config_mode:
            device.exit_config_mode()
        elif not is_in_enable_mode:
            device.enable()
        return
    if permission_level == 'user':
        if is_in_enable_mode:
            device.exit_enable_mode()
        elif is_in_config_mode:
            device.exit_config_mode()
            device.exit_enable_mode()
        return
    if permission_level == "configure terminal":
        if is_in_enable_mode:
            device.config_mode()
        else:
            device.enable()
            device.config_mode()
        return


def execute_commands(
        device_options: dict,
        commands: List[str],
        permission_level: PermissionLevel
) -> str:
    """
    Execute commands on a network device with a specified permission level.

    :param device_options: Dictionary containing device connection parameters.
    :param commands: List of commands to execute.
    :param permission_level: PermissionLevel enum representing the desired permission level.
    :return: Output generated by executing the commands.
    """
    output = ""
    with Connection(device_options) as device:
        change_permission(device, permission_level)
        if permission_level in ["user", "enable"]:
            output = send_commands(device, commands)
        elif permission_level in ["configure_terminal"]:
            output = send_config_commands(device, commands)
    return output


def send_commands(device: netmiko.BaseConnection, commands: List[str]) -> str:
    """
    Send a list of commands to a network device.
    the commands will be sent one by one and not togather.

    :param device: Netmiko connection object.
    :param commands: List of commands to send.
    :return: Output generated by executing the commands.
    """

    output = ""
    for command in commands:
        output += device.find_prompt()
        output += command
        output += '\n'
        output += device.send_command(command)
        output += '\n'
    return output


def send_config_commands(device: netmiko.BaseConnection, commands: List[str]) -> str:
    """
    Send a list of configuration commands to a network device.
    send the commands as togather in config mode.

    :param device: Netmiko connection object.
    :param commands: List of configuration commands to send.
    :return: Output generated by executing the commands.
    """

    output = ""
    output += device.find_prompt()
    output += device.send_config_set(commands)
    return output


class Connection:
    """
    A context manager for establishing and managing connections to network devices using Netmiko.

    usage - Use with a context manager (with Connection(...) as conn).
    """
    def __init__(self, device_options):
        self._device_options = device_options
        self._device = None

    def __enter__(self) -> netmiko.BaseConnection:
        self._device = netmiko.ConnectHandler(**self._device_options)
        return self._device

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._device.disconnect()
