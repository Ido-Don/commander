import os.path
import shutil

import mimesis
import pykeepass
import pytest

from NetworkCommander.device import Device, SUPPORTED_DEVICE_TYPES
from NetworkCommander.init import create_new_keepass_db
from NetworkCommander.keepass import KeepassDB, add_device_entry, get_all_device_entries, get_device_tags, \
    does_device_exist

KEEPASS_PASSWORD = "123"
POSSIBLE_TAGS = {'manhã', 'vivo', 'pelo', 'tia', 'assuntos', 'mexe', 'diabos', 'correcto', 'rapariga', 'socorro',
                 'trouxe', 'raparigas', 'liga', 'momentos', 'levar', 'papai', 'eu', 'morgan', 'acreditas', 'vim',
                 'chapéu', 'passagem', 'nos', 'gostei', 'ligo', 'cerca', 'governo', 'prender', 'apareceu', 'escolha',
                 'traz', 'daqui', 'olhos', 'respirar', 'levaram', 'sensação', 'sentado', 'acontecer', 'colega',
                 'inglaterra', 'pescoço', 'vídeo', 'deu', 'chá', 'imaginar', 'bebida', 'pé', 'ponham', 'unidade',
                 'esperança', 'suficiente', 'larga', 'nota', 'última', 'méxico', 'notícias', 'verão', 'faz',
                 'interessante', 'geral', 'uso', 'homens', 'lado', 'indo', 'vegas', 'estará', 'semana', 'bocadinho',
                 'chave', 'praia', 'giro', 'chegou', 'senhoras', 'somos', 'inocente', 'agradecer', 'inocente',
                 'excelente', 'esperava', 'está', 'dou', 'fumar', 'paris', 'poderia', 'dado', 'perdão', 'estado',
                 'limpa', 'tome', 'terem', 'mão', 'completo', 'lamento', 'posição', 'milhão', 'esqueça', 'mal', 'dra',
                 'irá', 'pode'}

internet = mimesis.Internet()
generic = mimesis.Generic()
Finance = mimesis.Finance()

POPULATED_DB_PATH = "populated_db.kdbx"


def get_test_device():
    username = generic.person.name()
    password = generic.person.password()
    name = f"{internet.hostname()}.{Finance.company()}{internet.top_level_domain()}"
    host = internet.ip_v4()
    port = internet.port()
    device_type = generic.random.choice(SUPPORTED_DEVICE_TYPES)
    device = Device(name, username, password, host, device_type, port)
    return device


def get_tag_list():
    tags = [generic.random.choice(POSSIBLE_TAGS) for _ in range(generic.random.randint(0, 10))]
    if not tags:
        tags = None
    return tags


def populate_db(keepass_db_path: str):
    if os.path.isfile(keepass_db_path):
        os.remove(keepass_db_path)
    create_new_keepass_db(keepass_db_path, KEEPASS_PASSWORD)
    with KeepassDB(keepass_db_path, KEEPASS_PASSWORD) as kp:
        for _ in range(300):
            device = get_test_device()
            tags = get_tag_list()
            add_device_entry(device, kp, tags)


class TestKeepass:

    @pytest.fixture
    def populated_db(self) -> str:
        if os.path.isfile(POPULATED_DB_PATH):
            return POPULATED_DB_PATH
        populate_db(POPULATED_DB_PATH)
        return POPULATED_DB_PATH

    def test_keepass_db_creation(self):
        test_db_path = "test_db.kdbx"
        with KeepassDB(test_db_path, KEEPASS_PASSWORD) as kp:
            assert os.path.isfile(test_db_path)

    def test_keepass_db_insertion(self, populated_db):
        insertion_test_kdbx = "insertion_" + populated_db
        shutil.copyfile(populated_db, insertion_test_kdbx)

        device = get_test_device()
        kp = pykeepass.PyKeePass(insertion_test_kdbx, KEEPASS_PASSWORD)
        add_device_entry(device, kp)
        entry = kp.find_entries(title=device.name)[0]
        assert entry.title == device.name
        assert entry.password == device.password
        assert entry.username == device.username
        assert entry.get_custom_property("host") == device.host
        assert entry.get_custom_property("port") == str(device.port)
        assert entry.get_custom_property("device_type") == device.device_type

    def test_keepass_db_insertion_with_tag(self, populated_db):
        # set up test environment
        insertion_test_kdbx = "insertion_tag_" + populated_db
        shutil.copyfile(populated_db, insertion_test_kdbx)

        device = get_test_device()
        tags = ["tag1", 'tag2']

        kp = pykeepass.PyKeePass(insertion_test_kdbx, KEEPASS_PASSWORD)

        # preform the operation
        add_device_entry(device, kp, tags)

        # find out if it was successful
        entry = kp.find_entries(title=device.name)[0]
        assert entry.title == device.name
        assert entry.password == device.password
        assert entry.username == device.username
        assert entry.get_custom_property("host") == device.host
        assert entry.get_custom_property("port") == str(device.port)
        assert entry.get_custom_property("device_type") == device.device_type
        assert entry.tags == tags

    def test_db_selection(self, populated_db):
        device = get_test_device()
        test_db = "selection_" + populated_db
        create_new_keepass_db(test_db, KEEPASS_PASSWORD)

        kp = pykeepass.PyKeePass(test_db, KEEPASS_PASSWORD)
        add_device_entry(device, kp)

        devices = get_all_device_entries(kp)
        assert devices == [device]

    def test_db_selection_with_tags(self, populated_db):
        test_db = "selection_tags_" + populated_db
        shutil.copyfile(populated_db, test_db)

        kp = pykeepass.PyKeePass(test_db, KEEPASS_PASSWORD)
        device = get_test_device()
        tags = get_tag_list()
        add_device_entry(device, kp, tags)

        devices = get_all_device_entries(kp, tags)
        assert devices == [device]

    def test_get_device_tags(self, populated_db):
        kp = pykeepass.PyKeePass(populated_db, KEEPASS_PASSWORD)
        tags = get_device_tags(kp)
        assert tags == POSSIBLE_TAGS

    def test_does_device_exist_false(self, populated_db):
        """
        this test check rather does_device_exist will catch that an entry is not in the db
        """
        test_db = "exist_" + populated_db
        shutil.copyfile(populated_db, test_db)
        kp = pykeepass.PyKeePass(test_db, KEEPASS_PASSWORD)

        # delete some random entry
        entry_to_delete = generic.random.choice(kp.entries)
        entry_to_delete_title = entry_to_delete.title
        entries_to_delete = kp.find_entries(title=entry_to_delete_title)
        for entry in entries_to_delete:
            kp.delete_entry(entry)

        # check if the random entry is still in the db
        assert not does_device_exist(entry_to_delete_title, kp)

    def test_does_device_exist_true(self, populated_db):
        """
        this test checks if the does_device_exist can find an entry that is in the database
        """
        kp = pykeepass.PyKeePass(populated_db, KEEPASS_PASSWORD)
        entry = generic.random.choice(kp.entries)
        assert does_device_exist(entry.title, kp)
