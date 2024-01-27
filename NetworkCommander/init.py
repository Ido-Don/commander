import json
import os
import shutil

from NetworkCommander.keepass import KeepassDB, DEVICE_GROUP_NAME


def delete_project_files(directory):
    if not os.path.isdir(directory):
        raise Exception(f"directory {directory} doesn't exist")
    shutil.rmtree(directory)


def init_program(directory, keepass_db_path, config_file_path):
    if is_initialized(directory, keepass_db_path, config_file_path):
        return
    if not os.path.isfile(config_file_path):
        with open(config_file_path, 'w') as config_file:
            json.dump({}, config_file)
    if not os.path.isdir(directory):
        os.mkdir(directory)
    if not os.path.isfile(keepass_db_path):
        create_new_keepass_db(keepass_db_path)


def create_new_keepass_db(keepass_db_path, keepass_password=None):
    with KeepassDB(keepass_db_path, keepass_password) as kp:
        kp.add_group(kp.root_group, DEVICE_GROUP_NAME)


def is_initialized(directory, keepass_db_path, config_file_path):
    if os.path.isdir(directory):
        return os.path.isfile(keepass_db_path) and os.path.isfile(config_file_path)
    return False
