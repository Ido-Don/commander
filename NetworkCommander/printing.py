from typing import Iterable

import typer


def print_objects(objects: Iterable, object_name: str):
    if not objects:
        typer.echo(f"there are 0 {object_name}")
        return

    typer.echo(f"{object_name}: ")
    number_of_objects = 0
    for obj in objects:
        number_of_objects += 1
        typer.echo(f"{obj}")
    typer.echo(f"there are {number_of_objects} {object_name}")