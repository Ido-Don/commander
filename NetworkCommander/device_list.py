from typing import List, Iterable

import typer

from NetworkCommander.device import Device


def print_devices(devices: Iterable[Device]):
    if not devices:
        typer.echo("there are 0 devices")
        return

    typer.echo("devices: ")
    number_of_devices = 0
    for device in devices:
        number_of_devices += 1
        typer.echo(f"{device}")
    typer.echo(f"there are {number_of_devices} devices")
