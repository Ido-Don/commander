import json
import os
import sys
from typing import Iterable, TextIO, List

import typer
import yaml

from networkcommander.commander_logging import commander_logger
from networkcommander.config import USER_CONFIG_FILE_PATH, config


def print_objects(objects: Iterable, object_name: str) -> None:
    """
    print objects in a specific format
    :param objects: the collection of the objects.
    :param object_name: the name of the objects
    """
    if not objects:
        typer.echo(f"there are 0 {object_name}")
        return

    typer.echo(f"{object_name}: ")
    number_of_objects = 0
    for obj in objects:
        number_of_objects += 1
        typer.echo(f"{str(obj)}")
    typer.echo(f"there are {number_of_objects} {object_name}")


def read_file(file: TextIO) -> List[str]:
    """
    this function reads the content of a file, cleans it and return the content of it.
    :param file: any file (for example: sys.stdin).
    :return: the lines this file contain.
    """
    user_inputs = file.readlines()
    user_inputs = [string.strip('\r\n ') for string in user_inputs]
    user_inputs = [string.replace('\4', '') for string in user_inputs]
    user_inputs = [string.replace("\26", '') for string in user_inputs]
    user_inputs = list(filter(bool, user_inputs))
    return user_inputs


def read_from_stdin():
    typer.echo("hit control-Z or control-D to continue")
    commands = read_file(sys.stdin)
    return commands


def convert_to_yaml(content: str):
    new_yaml = yaml.safe_load(content)
    return new_yaml


def load_user_config():
    """
    Load configuration settings from the user-specific configuration file.
    and update the application's configuration accordingly that lives in the config variable.

    Note: The configuration file is expected to be in JSON format.
    """
    commander_logger.info("loading user config from %s", USER_CONFIG_FILE_PATH)
    if os.path.isfile(USER_CONFIG_FILE_PATH):
        with open(USER_CONFIG_FILE_PATH, encoding="UTF-8") as json_file:
            commander_logger.info("successfully opened file located at %s", USER_CONFIG_FILE_PATH)
            file_content = json_file.read()
            if not file_content:
                commander_logger.info("file %s had no data", USER_CONFIG_FILE_PATH)
                return
            user_custom_config = json.loads(file_content)
            config.update(user_custom_config)
            commander_logger.info("finished loading user config")
