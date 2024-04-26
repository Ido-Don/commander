import mimesis

from networkcommander.device import DeviceType, Device

generic = mimesis.Generic()
internet = mimesis.Internet()


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
    username = generic.person.name()
    password = generic.person.password()
    ip = internet.ip_v4()
    name = f"{ip}{internet.top_level_domain()}"
    host = ip
    port = internet.port()
    device_type = generic.random.choice([device.value for device in DeviceType])
    device = Device(name, username, password, host, device_type, {'port': str(port)})
    return device


def get_tag_list():
    tags = generic.random.choices(POSSIBLE_TAGS, k=generic.random.randint(0, 10))
    if not tags:
        tags = None
    return tags

