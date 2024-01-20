from enum import Enum
from typing import Any, Dict


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


class supported_device(str, Enum):
    cisco_ios = "cisco_ios",
    cisco_ios_xe = "cisco_ios_xe",
    cisco_ios_telnet = "cisco_ios_telnet",
    cisco_ios_xe_telnet = "cisco_ios_xe_telnet"
