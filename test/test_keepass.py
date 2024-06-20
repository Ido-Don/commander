import os.path
import shutil
from typing import Set, List, Optional, Union
from test.logging_for_testing import fake_logger

from faker import Faker
from pykeepass.pykeepass import Entry
import pykeepass
import pytest

from networkcommander.init import create_new_keepass_db

from networkcommander.keepass import KeepassDB, add_device_entry, \
    does_device_exist, get_all_entries, is_entry_tagged_by_tags, \
    is_entry_tagged, tag_entry, untag_entry
from networkcommander.device import DeviceType, Device

faker = Faker()

POSSIBLE_TAGS = ['manhã', 'vivo', 'pelo', 'tia', 'assuntos', 'mexe', 'diabos', 'correcto', 'rapariga', 'socorro',
                 'trouxe', 'raparigas', 'liga', 'momentos', 'levar', 'papai', 'eu', 'morgan', 'acreditas', 'vim',
                 'chapéu', 'passagem', 'nos', 'gostei', 'ligo', 'cerca', 'governo', 'prender', 'apareceu', 'escolha',
                 'traz', 'daqui', 'olhos', 'respirar', 'levaram', 'sensação', 'sentado', 'acontecer', 'colega',
                 'inglaterra', 'pescoço', 'vídeo', 'deu', 'chá', 'imaginar', 'bebida', 'pé', 'ponham', 'unidade',
                 'esperança', 'suficiente', 'larga', 'nota', 'última', 'méxico', 'notícias', 'verão', 'faz',
                 'interessante', 'geral', 'uso', 'homens', 'lado', 'indo', 'vegas', 'estará', 'semana', 'bocadinho',
                 'chave', 'praia', 'giro', 'chegou', 'senhoras', 'somos', 'inocente', 'agradecer', 'inocente',
                 'excelente', 'esperava', 'está', 'dou', 'fumar', 'paris', 'poderia', 'dado', 'perdão', 'estado',
                 'limpa', 'tome', 'terem', 'mão', 'completo', 'lamento', 'posição', 'milhão', 'esqueça', 'mal', 'dra',
                 'irá', 'pode']


def get_test_device():
    username = faker.user_name()
    password = faker.password()
    ip = faker.ipv4()
    name = faker.hostname()
    host = ip
    port = faker.port_number()
    device_type = faker.random_element([str(device) for device in DeviceType])
    device = Device(name, username, password, host,
                    device_type, {'port': str(port)})
    return device


def get_tag_list():
    tags = faker.random_choices(POSSIBLE_TAGS)
    if not tags:
        tags = None
    return tags


KEEPASS_PASSWORD = "123"
POSSIBLE_NAMES = list(POSSIBLE_TAGS)
POPULATED_DB_PATH = "populated_db.kdbx"
READ_ONLY_KP_PATH = "read_only_keepass.kdbx"
READ_ONLY_KP = pykeepass.PyKeePass(
    READ_ONLY_KP_PATH, KEEPASS_PASSWORD
)  # type: ignore


def populate_db(keepass_db_path: str):
    if os.path.isfile(keepass_db_path):
        os.remove(keepass_db_path)
    create_new_keepass_db(keepass_db_path, fake_logger, KEEPASS_PASSWORD)
    with KeepassDB(keepass_db_path, KEEPASS_PASSWORD) as kp:
        for _ in range(300):
            device = get_test_device()
            tags = get_tag_list()
            add_device_entry(kp, device, tags)  # type: ignore


class TestKeepass:

    @pytest.fixture
    def populated_db(self) -> str:
        if os.path.isfile(POPULATED_DB_PATH):
            return POPULATED_DB_PATH
        populate_db(POPULATED_DB_PATH)
        return POPULATED_DB_PATH

    def test_keepass_db_creation(self):
        test_db_path = "test_db.kdbx"
        with KeepassDB(test_db_path, KEEPASS_PASSWORD):
            assert os.path.isfile(test_db_path)

    def test_keepass_db_insertion(self, populated_db):
        insertion_test_kdbx = "insertion_" + populated_db
        shutil.copyfile(populated_db, insertion_test_kdbx)

        device = get_test_device()
        kp = pykeepass.PyKeePass(insertion_test_kdbx, KEEPASS_PASSWORD)
        add_device_entry(kp, device)
        entry = kp.find_entries(title=device.name)[0]  # type: ignore
        assert entry.title == device.name
        assert entry.password == device.password
        assert entry.username == device.username
        assert entry.get_custom_property("host") == device.host
        assert entry.get_custom_property("port") == str(
            device.optional_parameters['port'])
        assert entry.get_custom_property(
            "device_type") == str(device.device_type)

    def test_keepass_db_insertion_with_tag(self, populated_db):
        # set up test environment
        insertion_test_kdbx = "insertion_tag_" + populated_db
        shutil.copyfile(populated_db, insertion_test_kdbx)

        device = get_test_device()
        tags = ["tag1", 'tag2']

        kp = pykeepass.PyKeePass(insertion_test_kdbx, KEEPASS_PASSWORD)

        # preform the operation
        add_device_entry(kp, device, tags)

        # find out if it was successful
        entry = kp.find_entries(title=device.name)[0]  # type: ignore
        assert entry.title == device.name
        assert entry.password == device.password
        assert entry.username == device.username
        assert entry.get_custom_property("host") == device.host
        assert entry.get_custom_property("port") == str(
            device.optional_parameters['port'])
        assert entry.get_custom_property(
            "device_type") == str(device.device_type)
        assert entry.tags == tags

    def test_does_device_exist_false(self, populated_db):
        """
        this test check rather does_device_exist will catch that an entry is not in the db
        """
        test_db = "exist_" + populated_db
        shutil.copyfile(populated_db, test_db)
        kp = pykeepass.PyKeePass(test_db, KEEPASS_PASSWORD)
        entries = kp.entries
        print(entries)
        # delete some random entry
        assert isinstance(entries, list)
        assert len(entries) > 1
        entry_to_delete = faker.random_element(entries)
        entry_to_delete_title = entry_to_delete.title
        entries_to_delete = kp.find_entries(title=entry_to_delete_title)
        for entry in entries_to_delete:  # type: ignore
            kp.delete_entry(entry)

        # check if the random entry is still in the db
        assert not does_device_exist(kp, entry_to_delete_title)

    def test_does_device_exist_true(self, populated_db):
        """
        this test checks if the does_device_exist can find an entry that is in the database
        """
        kp = pykeepass.PyKeePass(populated_db, KEEPASS_PASSWORD)
        print(kp.entries)

        entry = faker.random_element(kp.entries)  # type: ignore
        assert does_device_exist(kp, entry.title)

    def test_get_all_entries(self, populated_db):
        kp = pykeepass.PyKeePass(populated_db, KEEPASS_PASSWORD)
        entries = get_all_entries(kp, fake_logger)
        assert entries == tuple(kp.entries)  # type: ignore

    @pytest.mark.parametrize(
        ("entry", "tag", "expected_tags"),
        [
            (
                Entry("",
                      "",
                      "",
                      tags=["hello"],
                      kp=READ_ONLY_KP),
                "world",
                ["hello", "world"]
            ),
            (
                Entry("",
                      "",
                      "",
                      kp=READ_ONLY_KP),
                "world",
                ["world"]
            ),
        ]
    )
    def test_tag_entry(self, entry: Entry, tag: str, expected_tags: Optional[List[str]]):
        tag_entry(entry, tag)
        assert entry.tags == expected_tags

    @pytest.mark.parametrize(
        ("entry", "tag", "expected_tags"),
        [
            (
                Entry("",
                      "",
                      "",
                      tags=["hello"],
                      kp=READ_ONLY_KP),
                "hello",
                ""
            ),
            (
                Entry("",
                      "",
                      "",
                      tags=["hello", "world"],
                      kp=READ_ONLY_KP),
                "world",
                ["hello"]
            ),
            (
                Entry("",
                      "",
                      "",
                      tags=["hello", "world", "item2"],
                      kp=READ_ONLY_KP),
                "world",
                ["hello", "item2"]
            ),
        ]
    )
    def test_untag_entry(self, entry: Entry, tag: str, expected_tags: Optional[Union[List[str], str]]):
        untag_entry(entry, tag)
        assert entry.tags == expected_tags


@pytest.mark.parametrize(
    ("entry", "tags", "should_match"),
    [
        (
            Entry("",
                  "",
                  "",
                  kp=READ_ONLY_KP),
            {"hello"},
            False
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["hello", "item2"],
                  kp=READ_ONLY_KP),
            {"hello", "world", "item3"},
            False
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["hello", "item3"],
                  kp=READ_ONLY_KP),
            {"hello", "world", "item3"},
            False
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["item1", 'world', "item3"],
                  kp=READ_ONLY_KP),
            {"hello", "item4"},
            False
        ),
        (
            Entry("",
                  "",
                  "",
                  kp=READ_ONLY_KP),
            {"hello", "world", "python"},
            False
        ),
        (
            None,
            {"hello", "world"},
            False
        ),
        (
            Entry("",
                  "",
                  "",
                  kp=READ_ONLY_KP),
            {},
            True
        ),
        (
            Entry("",
                  "",
                  "",
                  kp=READ_ONLY_KP),
            None,
            True
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["hello", 'world'],
                  kp=READ_ONLY_KP),
            {"hello"},
            True
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["hello", 'world', "item3"],
                  kp=READ_ONLY_KP),
            {"hello", "item3"},
            True
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["hello", 'world', "item3"],
                  kp=READ_ONLY_KP),
            {"hello", 'world', "item3"},
            True
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["hello", 'world', "item3"],
                  kp=READ_ONLY_KP),
            {"hello", 'world'},
            True
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["hello", 'world', "item3"],
                  kp=READ_ONLY_KP),
            {"item3", 'world'},
            True
        )
    ]
)
def test_is_entry_tagged_by_tag_set(entry: Entry, tags: Set[str], should_match: bool):
    assert is_entry_tagged_by_tags(tags)(entry) == should_match


@pytest.mark.parametrize(
    ("entry", "tag", "should_match"),
    [
        (
            Entry("",
                  "",
                  "",
                  kp=READ_ONLY_KP),
            "hello",
            False
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["item1", "item2", 'item3'],
                  kp=READ_ONLY_KP),
            "item4",
            False
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["item1", "item2"],
                  kp=READ_ONLY_KP),
            "item3",
            False
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["item1"],
                  kp=READ_ONLY_KP),
            "item3",
            False
        ),
        (
            None,
            "hello",
            False
        ),
        (
            Entry("",
                  "",
                  "",
                  kp=READ_ONLY_KP),
            "",
            True
        ),
        (
            Entry("",
                  "",
                  "",
                  kp=READ_ONLY_KP),
            None,
            True
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["hello", 'world'],
                  kp=READ_ONLY_KP),
            "hello",
            True
        ),
        (
            Entry("",
                  "",
                  "",
                  tags=["hello", 'world', "item3"],
                  kp=READ_ONLY_KP),
            "hello",
            True
        )
    ]
)
def test_is_entry_tagged(entry: Entry, tag: str, should_match: bool):
    assert is_entry_tagged(tag)(entry) == should_match
