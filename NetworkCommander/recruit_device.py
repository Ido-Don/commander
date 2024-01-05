import json
from typing import List

import typer
from rich.prompt import Prompt

from NetworkCommander.device import Device
from NetworkCommander.device import SUPPORTED_DEVICE_TYPES


def retrieve_device_from_input(reserved_device_names: List[str]) -> Device:
    name = Prompt.ask("Device's name")
    while name in reserved_device_names:
        typer.echo(
            f"Sorry you cant pick {name}, it is already in database."
            f" to change a recorde use commander change",
            err=True
        )
        name = Prompt.ask("Device's name")

    username = Prompt.ask("Device's username")
    if not username:
        username = ''
    password = Prompt.ask("Device's password", password=True)
    if not password:
        password = ''
    host = Prompt.ask("Device's ip/hostname")
    device_type = Prompt.ask("Device's software Type", choices=SUPPORTED_DEVICE_TYPES, default=SUPPORTED_DEVICE_TYPES[0])
    default_port = "22"
    if 'telnet' in device_type:
        default_port = "23"
    port = Prompt.ask("Device's port", default=default_port, show_default=True)
    device = Device(
        name=name,
        username=username,
        password=password,
        host=host,
        port=port,
        device_type=device_type
    )
    return device


def clear_device(device):
    if device:
        return True
    return False


def retrieve_device_from_file(device_names: List[str], file: typer.FileText):
    device_json = json.load(file)
    device = Device.model_validate(device_json)
    if device.name in device_names:
        raise ValueError(f"⛔ device {device.name} is already in database.")

    if device.device_type not in SUPPORTED_DEVICE_TYPES:
        raise ValueError(f"⛔ device {device.device_type} is not supported.")
    return device
