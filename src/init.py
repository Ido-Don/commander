import os
from pykeepass import pykeepass

from src.device import DataBase


def init_program(commander_directory, keepass_db_path, keepass_password):
    if is_initialized(keepass_db_path, keepass_password):
        return
    if not os.path.isdir(commander_directory):
        os.mkdir(commander_directory)
    if not os.path.isfile(keepass_db_path):
        create_new_keepass_db(keepass_db_path, keepass_password)


def create_new_keepass_db(keepass_db_path, keepass_password):
    with DataBase(keepass_db_path, keepass_password) as kp:
        kp.add_group(kp.root_group, "devices")


def is_initialized(directory, keepass_db_path):
    if os.path.isdir(directory):
        return os.path.isfile(keepass_db_path)
    return False
