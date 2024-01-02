from typing import List

import netmiko


def change_permission(device: netmiko.BaseConnection, permission_level: str):
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


def execute_commands(device_options: dict, commands: List[str], permission_level: str) -> str:
    output = ""
    with Connection(device_options) as device:
        change_permission(device, permission_level)
        if permission_level in ["user", "enable"]:
            output = gather_output(device, commands)
        elif permission_level in ["configure terminal"]:
            output = send_config_commands(device, commands)
    return output


def gather_output(device: netmiko.BaseConnection, commands: List[str]) -> str:
    output = ""
    for command in commands:
        output += device.find_prompt()
        output += command
        output += '\n'
        output += device.send_command(command)
        output += '\n'
    return output


def send_config_commands(device: netmiko.BaseConnection, commands: List[str]) -> str:
    output = ""
    output += device.find_prompt()
    output += device.send_config_set(commands)
    return output


class Connection:
    def __init__(self, device_options):
        self._device_options = device_options

    def __enter__(self) -> netmiko.BaseConnection:
        self._device = netmiko.ConnectHandler(**self._device_options)
        return self._device

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._device.disconnect()
