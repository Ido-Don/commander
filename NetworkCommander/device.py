from enum import Enum
from typing import Any, Dict, Tuple, Optional


def normalize_string_input(value: Any):
    if not value:
        return ""
    return str(value)


class Device:
    """
    netmiko.ConnectHandler takes in a lot of arguments that change from execution to execution.
    this class is here to hold the data netmiko.ConnectHandler needs to run.
    """

    def __init__(self, name: str, username: str, password: str, host: str, device_type: str, port: int = None):
        self.name = name
        self.username = normalize_string_input(username)
        self.password = normalize_string_input(password)
        self.host = host
        self.device_type = device_type
        if port:
            if port < 0 or port > 65535:
                raise ValueError("port cant be below 0 or below 65535")
            self.port = port
        else:
            self.port = None

    def __str__(self):
        device_string = ''
        if self.name:
            device_string += self.name
        if self.device_type:
            device_string += f'({self.device_type})'
        if device_string:
            device_string += ' -> '
        device_string += self.get_ssh_string()
        return device_string

    def __eq__(self, other):
        if not isinstance(other, Device):
            return False
        return (
                self.name == other.name and
                self.username == other.username and
                self.password == other.password and
                self.host == other.host and
                self.device_type == other.device_type and
                self.port == other.port
        )

    def __hash__(self):
        return hash((self.name, self.username, self.password, self.host, self.port, self.device_type))

    def get_ssh_string(self):
        """
        this function takes the data in the class and convert it to a valid ssh string.
        example - Device(host="google", username="root", port="22"...).get_ssh_string() -> root@google:22
        then you can use it with ssh command to connect to the remote device.
        example - ssh root@google:22

        :return: an ssh string (username@{ip/hostname}:port)
        """
        ssh_string = ""

        if self.username:
            ssh_string += f"{self.username}@"

        ssh_string += self.host

        if self.port:
            ssh_string += f":{self.port}"

        return ssh_string

    @property
    def device_options(self) -> Dict[str, str]:
        """
        netmiko.ConnectionHandler() accepts only arguments.
        this property convert the data in this class to arguments netmiko.ConnectionHandler() can accept.
        example - netmiko.ConnectionHandler(**device.device_options).
        :return: a dictionary containing the arguments netmiko.ConnectionHandler() needs to run
        """
        json_dump = {
            "username": self.username,
            "password": self.password,
            "host": self.host,
            "device_type": self.device_type
        }
        if self.port:
            json_dump['port'] = str(self.port)
        return json_dump

    @staticmethod
    def from_string(device: str):
        if not device:
            raise ValueError(f"you can't have an empty device")
        device = device.strip(' \n')
        device_descriptor, connection_string = deconstruct_device(device)
        username, hostname, port = deconstruct_connection_string(connection_string)
        device_type = None
        if device_descriptor:
            name, device_type = deconstruct_device_descriptor(device_descriptor)
        else:
            name = hostname
        if not device_type:
            device_type = supported_device_type.default
        return Device(name, username, "", hostname, device_type, port)


def deconstruct_device_descriptor(device_descriptor: str) -> Tuple[str, Optional[str]]:
    device_type_appear = any(f'({device_type})' in device_descriptor for device_type in supported_device_type)
    perianthes_appear = '(' in device_descriptor or ')' in device_descriptor
    if device_type_appear:
        name, device_type = device_descriptor.split('(')
        device_type = device_type.rstrip(')')
        return name, device_type

    elif perianthes_appear:
        raise NotImplemented(f"sorry we don't support '{device_descriptor}' software type.\n"
                             f"the supported types are {', '.join(supported_device_type)}")

    return device_descriptor, None


def deconstruct_device(device: str):
    if device.count('->') > 1:
        raise Exception(f"{device} has more then 1 '->'")
    if device.count('\n') > 1:
        raise Exception(f"device {device} shouldn't have a line break.")
    if '->' in device:
        device_descriptor, connection_string = device.split('->')
        device_descriptor = device_descriptor.strip()
        connection_string = connection_string.strip()
        return device_descriptor, connection_string
    else:
        connection_string: str = device
        return None, connection_string


def deconstruct_socket_id(socket_id: str) -> Tuple[str, int]:
    """
    this function returns the variables contained inside an IPv4 socket_id
    :param socket_id: a hostname or ip (IPv4) with a port, like: 1.1.1.1:234, 12312:22, google.com:5000
    :raise: ValueError if the socket_id is not a real one or doesn't contain a port
     (for example, kjnjsl::: is not a valid socket id)
    :return: the hostname or ip address and port number
    """
    if socket_id.count(':') != 1:
        raise ValueError(f"{socket_id} is not a valid IPv4 socket id, it has more then 1 ':'.")
    hostname, port = socket_id.split(':')
    if not port or not port.isnumeric():
        raise ValueError(f"{socket_id} doesn't contain a valid port number")
    port = int(port)
    if 0 > port or port > 65535:
        raise ValueError(f"{port} is not in the valid port range")

    return hostname, port


class supported_device_type(str, Enum):
    default = "cisco_ios"
    cisco_ios = "cisco_ios",
    cisco_ios_xe = "cisco_ios_xe",
    cisco_ios_telnet = "cisco_ios_telnet",
    cisco_ios_xe_telnet = "cisco_ios_xe_telnet"


def deconstruct_connection_string(connection: str) -> Tuple[Optional[str], str, Optional[int]]:
    """
    this function extracts the variables of an ssh connection string from the string.
    :param connection: a string representing a session with a remote device
    (example: root@google.com:22, alice@exemple.com, YouTube.com:5000, 1.1.1.1)
    :return: username, hostname, port
    :raises: ValueError if the connection string is invalid
    """
    if connection.count('@') > 1:
        raise ValueError(f"{connection} is not a valid ssh connection string, it has more then 1 '@'.")

    # extract username and socket_id from connection
    if '@' in connection:
        username, socket_id = connection.split('@')

        if not username:
            username = None

    else:
        socket_id = connection
        username = None

    # extract hostname and port from socket_id
    port = None

    does_socket_id_ends_with_colon = socket_id[-1] == ':'
    if does_socket_id_ends_with_colon:
        hostname = socket_id[:-2]

    elif ':' in socket_id and not does_socket_id_ends_with_colon:
        hostname, port = deconstruct_socket_id(socket_id)

    else:
        hostname = socket_id

    # return the connection variables
    return username, hostname, port
