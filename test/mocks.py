from faker import Faker

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
    device = Device(name, username, password, host, device_type, {'port': str(port)})
    return device


def get_tag_list():
    tags = faker.random_choices(POSSIBLE_TAGS)
    if not tags:
        tags = None
    return tags
