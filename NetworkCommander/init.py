import os
import shutil

from NetworkCommander.keepass import KeepassDB, DEVICE_GROUP_NAME


def delete_project_files(directory):
    if not os.path.isdir(directory):
        raise Exception(f"directory {directory} doesn't exist")
    shutil.rmtree(directory)


def init_program(directory, keepass_db_path):
    if is_initialized(directory, keepass_db_path):
        return
    if not os.path.isdir(directory):
        os.mkdir(directory)
    if not os.path.isfile(keepass_db_path):
        create_new_keepass_db(keepass_db_path)


def create_new_keepass_db(keepass_db_path):
    with KeepassDB(keepass_db_path) as kp:
        kp.add_group(kp.root_group, DEVICE_GROUP_NAME)


def is_initialized(directory, keepass_db_path):
    if os.path.isdir(directory):
        return os.path.isfile(keepass_db_path)
    return False
