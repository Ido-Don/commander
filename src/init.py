import os

from pykeepass import pykeepass

from src.global_variables import COMMANDER_DIRECTORY, KEEPASS_DB_PATH, KEEPASS_PASSWORD


def init_program():
    os.mkdir(COMMANDER_DIRECTORY)
    create_new_keepass_db()


def create_new_keepass_db():
    kp = pykeepass.create_database(KEEPASS_DB_PATH, password=KEEPASS_PASSWORD)
    kp.save()

