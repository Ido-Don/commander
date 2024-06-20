"""
this file contains function that help in the initialization process.
"""
import json
import os
import shutil
from logging import Logger
from typing import Any, Dict, Optional

import rich

from networkcommander.keepass import KeepassDB
from networkcommander.config import DEVICE_GROUP_NAME
from networkcommander.utils import is_file_json


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


def init_commander(config: Dict[str, Any], logger: Logger, keepass_password=None):
    """
    This function, if not present before, will create a new commander folder,
    a new user config file and a new keepass database
    :param config: a dictionary containing
    :param logger:
    :param keepass_password:
    :return:
    """
    logger.info("starting to initialize commander")
    commander_directory = config["commander_directory"]
    keepass_db_path = config["keepass_db_path"]
    config_file_path = config["config_file_path"]

    logger.debug("checking if commander is initialized")
    if is_initialized(commander_directory, keepass_db_path, config_file_path, logger):
        logger.debug("commander is already initialized")
        return
    logger.debug("commander is not initialized")

    if os.path.isfile(commander_directory):
        raise NotADirectoryError(
            f"{commander_directory} is a file and not a folder")

    if not os.path.exists(commander_directory):
        logger.debug("the commander directory does not exist")
        os.makedirs(commander_directory)
        rich.print(f"created a directory in {commander_directory}")
        logger.debug(f"created a directory in {commander_directory}")

    if not os.path.isfile(config_file_path):
        with open(config_file_path, 'w', encoding="utf-8") as config_file:
            json.dump(config, config_file, indent=2)
        rich.print(f"created a config file in {config_file_path}")
        logger.debug(f"created a config file in {config_file_path}")

    if not os.path.isfile(keepass_db_path):
        create_new_keepass_db(keepass_db_path, logger, keepass_password)
        rich.print(f"created a database in {keepass_db_path}")


def create_new_keepass_db(
        keepass_db_path: str,
        logger: Logger,
        keepass_password: Optional[str] = None
):
    """
    this function creates a new keepass database with a group.
    :param logger:
    :param keepass_db_path: the path to the new keepass db
    :param keepass_password: the new keepass password
    """
    logger.info(f"creating a new database in {keepass_db_path}")
    with KeepassDB(keepass_db_path, keepass_password) as kp:
        logger.debug(
            f"added a new group named {DEVICE_GROUP_NAME} to the database")
        kp.add_group(kp.root_group, DEVICE_GROUP_NAME)


def is_initialized(directory: str, keepass_db_path: str, config_file_path: str, logger: Logger):
    """
    this function checks if the commander directory is properly initialized
    :param logger:
    :param directory: the parent directory
    :param keepass_db_path: the keepass database path
    :param config_file_path: the commander config file path
    :return: true if everything is initialized correctly and false otherwise
    """
    logger.info("checking if commander is initialized")
    if not os.path.isdir(directory):
        logger.debug(
            f"commander is not initialized in this folder {directory}")
        return False
    logger.debug(f"commander is initialized in this folder {directory}")
    if not os.path.isfile(keepass_db_path):
        logger.debug(
            f"commander is not initialized with this db {keepass_db_path}")
        return False
    logger.debug(f"commander is initialized with this db {keepass_db_path}")
    if not is_file_json(config_file_path):
        logger.debug(
            f"commander is not initialized with this user file {config_file_path}")
        return False
    logger.debug(
        f"commander is initialized with this user file {config_file_path}")
    logger.info("commander is initialized")
    return True
