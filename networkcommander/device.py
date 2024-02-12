import dataclasses
from enum import Enum
from typing import Dict, Tuple, Optional

from networkcommander.config import config


@dataclasses.dataclass(frozen=True, order=True)
class Device:
    """
    netmiko.ConnectHandler takes in a lot of arguments that change from execution to execution.
    this class is here to hold the data netmiko.ConnectHandler needs to run par device.
    """
    name: str
    username: str
    password: str
    host: str
    device_type: str
    optional_parameters: Dict[str, str]

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

        if 'port' in self.optional_parameters:
            ssh_string += f":{self.optional_parameters['port']}"

        return ssh_string

    @property
    def device_options(self) -> Dict[str, str]:
        """
        this property convert the data in this class to
        arguments netmiko.ConnectionHandler() can accept.
        example - netmiko.ConnectionHandler(**device.device_options).
        :return: a dictionary containing the arguments netmiko.ConnectionHandler() needs to run
        """
        return {
            "username": self.username,
            "password": self.password,
            "host": self.host,
            "device_type": self.device_type,
            **self.optional_parameters
        }

    @staticmethod
    def from_string(device: str):
        """
        this function convert a string in the format:
            {name}({device_type}) -> {username}@{hostname}:{port}
        to a Device
        :param device: a string representing a device in this format
        {name}({device_type}) -> {username}@{hostname}:{port}
        :return: a device
        """
        if not device:
            raise ValueError("you can't have an empty device")
        device = device.strip(' \n')
        device_descriptor, connection_string = deconstruct_device(device)
        username, hostname, port = deconstruct_connection_string(connection_string)
        device_type = None
        if device_descriptor:
            name, device_type = deconstruct_device_descriptor(device_descriptor)
        else:
            name = hostname
        if not device_type:
            device_type = config["default_device_type"]
        optional_parameters = {}
        if port:
            optional_parameters = {
                "port": str(port)
            }
        return Device(name, username, "", hostname, device_type, optional_parameters)


def deconstruct_device_descriptor(device_descriptor: str) -> Tuple[str, Optional[str]]:
    device_type_appear = any(f'({device_type})' in device_descriptor for device_type in SupportedDevice)
    perianthes_appear = '(' in device_descriptor or ')' in device_descriptor
    if device_type_appear:
        name, device_type = device_descriptor.split('(')
        device_type = device_type.rstrip(')')
        return name, device_type

    if perianthes_appear:
        raise NotImplementedError(f"sorry we don't support '{device_descriptor}' software type.\n"
                                  f"the supported types are {', '.join(SupportedDevice)}")

    return device_descriptor, None


def deconstruct_device(device: str):
    if device.count('->') > 1:
        raise ValueError(f"{device} has more then 1 '->'")
    if device.count('\n') > 1:
        raise ValueError(f"device {device} shouldn't have a line break.")
    if '->' in device:
        device_descriptor, connection_string = device.split('->')
        device_descriptor = device_descriptor.strip()
        connection_string = connection_string.strip()
        return device_descriptor, connection_string
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


class SupportedDevice(str, Enum):
    CISCO_IOS = "cisco_ios"
    CISCO_IOS_XE = "cisco_ios_xe"
    CISCO_IOS_TELNET = "cisco_ios_telnet"
    CISCO_IOS_XE_TELNET = "cisco_ios_xe_telnet"


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
