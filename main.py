import logging
import sys
from getpass import getpass
from typing import Annotated, Optional, TypeAlias

import typer

from src.deploy import deploy_commands_on_devices
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


@app.command(help="deploy command to all the devices in your database")
def deploy(command_file: str, permission_level: str = "user"):
    deploy_commands_on_devices(command_file, permission_level)


@app.command(name="list", help="list all the devices in your command")
def list_devices():
    keepass_password = getpass("enter keepass database master password: ")
    device_list = get_device_list(keepass_password, KEEPASS_DB_PATH, COMMANDER_DIRECTORY)
    logger.info(device_list)


@app.command(help="add a device to the list of devices")
def recruit(file: Annotated[Optional[str], typer.Argument()] = None):
    keepass_password = getpass("enter keepass database master password: ")
    if not is_initialized(KEEPASS_DB_PATH, keepass_password):
        init_program(COMMANDER_DIRECTORY, KEEPASS_DB_PATH, keepass_password)
    recruit_device(file, KEEPASS_DB_PATH, keepass_password)


def main():
    app()


if __name__ == '__main__':
    main()
