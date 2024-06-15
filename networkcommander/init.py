import json
import os
import shutil
from logging import Logger

import rich

from networkcommander.keepass import KeepassDB
from networkcommander.config import DEVICE_GROUP_NAME


def delete_project_files(directory: str, logger: Logger):
    """
    Delete all the local commander files.
    :param directory: the folder all the project files live in
    :param logger: the logger the function will use.
    """
    logger.info(f"starting to delete directory: {directory}")
    rich.print(f"deleting directory: {directory}")
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"directory {directory} doesn't exist")
    shutil.rmtree(directory)
    logger.info(f"finished deleting directory: {directory}")


def init_program(directory, keepass_db_path, config_file_path, config):
    if is_initialized(directory, keepass_db_path, config_file_path):
        return
    os.makedirs(directory, exist_ok=True)
    if not os.path.isfile(config_file_path):
        with open(config_file_path, 'w', encoding="utf-8") as config_file:
            json.dump(config, config_file, indent=2)
    if not os.path.isfile(keepass_db_path):
        create_new_keepass_db(keepass_db_path)


def create_new_keepass_db(keepass_db_path: str, keepass_password=None):
    with KeepassDB(keepass_db_path, keepass_password) as kp:
        kp.add_group(kp.root_group, DEVICE_GROUP_NAME)


def is_initialized(directory, keepass_db_path, config_file_path):
    if os.path.isdir(directory):
        return os.path.isfile(keepass_db_path) and os.path.isfile(config_file_path)
    return False
