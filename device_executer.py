import json
from typing import List
import netmiko


def enter_enable_mode(callback):
    def enable(device: netmiko.BaseConnection):
        device.enable()
        callback(device)

    return enable


def enter_configure_terminal_mode(callback):
    def configure_terminal(device: netmiko.BaseConnection):
        device.enable()
        device.config_mode()
        callback(device)

    return configure_terminal


def enter_user_mode(callback):
    def user(device: netmiko.BaseConnection):
        device.exit_enable_mode()
        callback(device)

    return user


def execute_script(commands, device_options, output_file_path, permission_level="user"):
    write_output = handle_result(output_file_path)
    execute = execute_commands(commands, write_output)
    permission_escalation = escalate_permission(execute, permission_level)

    connect(device_options, permission_escalation)


def escalate_permission(callback, permissions):
    permission_escalation = None
    if permissions == "enable":
        permission_escalation = enter_enable_mode(callback)
    if permissions == "configure terminal":
        permission_escalation = enter_configure_terminal_mode(callback)
    if permissions == "user":
        permission_escalation = enter_user_mode(callback)
    return permission_escalation


def handle_result(output_file_path: str):
    def write_result(result):
        with open(output_file_path, 'w') as output_file:
            output_file.write(result)

    return write_result


def execute_commands(commands: List[str], result_callback):
    def execute(device: netmiko.BaseConnection):
        result = device.send_config_set(commands)
        result_callback(result)

    return execute


def connect(device_options, callback):
    device = netmiko.ConnectHandler(**device_options)
    callback(device)
    device.disconnect()
