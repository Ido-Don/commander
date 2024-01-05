from typing import List

import typer
from rich.prompt import Prompt

from device import Device
from device import SUPPORTED_DEVICE_TYPES


def retrieve_device_from_input(reserved_device_names: List[str]):
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
