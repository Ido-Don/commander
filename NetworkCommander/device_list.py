from typing import List

import typer

from NetworkCommander.device import Device


def print_devices(devices: List[Device]):
    if not devices:
        typer.echo("there are 0 devices")
        return

    typer.echo("devices: ")
    for device in devices:
        typer.echo(f"🖥️ {device}")
    typer.echo(f"there are {len(devices)} devices")
