import os

from src.device import DataBase


def init_program(directory, keepass_db_path):
    if is_initialized(directory, keepass_db_path):
        return
    if not os.path.isdir(directory):
        os.mkdir(directory)
    if not os.path.isfile(keepass_db_path):
        create_new_keepass_db(keepass_db_path)


def create_new_keepass_db(keepass_db_path):
    with DataBase(keepass_db_path) as kp:
        kp.add_group(kp.root_group, "devices")


def is_initialized(directory, keepass_db_path):
    if os.path.isdir(directory):
        return os.path.isfile(keepass_db_path)
    return False
