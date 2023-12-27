import logging
import sys
from typing import Annotated, Optional, TypeAlias

import typer

from src.deploy import deploy_commands_on_devices
from src.device import DataBase
from src.device_list import get_device_list
from src.global_variables import COMMANDER_DIRECTORY, KEEPASS_DB_PATH
from src.init import is_initialized, init_program
from src.recruit_device import recruit_device

logger = logging.Logger("commander")
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel("INFO")
logger.addHandler(handler)

app = typer.Typer()


device_entry_type: TypeAlias = dict[str, str | dict[str, str]]


def commands_reader(command_file_path):
    with open(command_file_path) as commands_file:
        commands = commands_file.readlines()
        commands = [command.strip("\n ") for command in commands]
        commands = filter(lambda command: is_valid_command(command), commands)
        commands = list(commands)
    return commands


def is_valid_command(command: str):
    if not command:
        return False
    if command[0] != '#':
        return False
    return True


@app.command(help="deploy command to all the devices in your database")
def deploy(command_file: str, permission_level: str = "user"):
    if not is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        logger.error("program is not initialized! please run commander init!")
        return

    commands = commands_reader(command_file)
    deploy_commands_on_devices(commands, permission_level, logger)


@app.command(name="list", help="list all the devices in your command")
def list_devices():
    if not is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH)
    with DataBase(KEEPASS_DB_PATH) as kp:
        device_list = get_device_list(kp)
    logger.info(device_list)


@app.command(help="add a device to the list of devices")
def recruit(file: Annotated[Optional[str], typer.Argument()] = None):
    if not is_initialized(COMMANDER_DIRECTORY, KEEPASS_DB_PATH):
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH)
    recruit_device(file, KEEPASS_DB_PATH, logger)


def main():
    app()


if __name__ == '__main__':
    main()
