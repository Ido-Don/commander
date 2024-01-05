from typing import Optional, Any, Dict
from pydantic import BaseModel


class Device(BaseModel):
    """
    netmiko.ConnectHandler takes in a lot of arguments that change from execution to execution.
    this class is here to hold the data netmiko.ConnectHandler needs to run.
    """
    name: str
    username: str
    password: str
    host: str
    device_type: str
    port: Optional[str] = None

    def __str__(self):
        device_string = f"{self.name}({self.device_type}) -> {self.get_ssh_string()}"
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

        if self.port:
            ssh_string += f":{self.port}"

        return ssh_string

    @property
    def device_options(self) -> Dict[str, Any]:
        """
        netmiko.ConnectionHandler() accepts only arguments.
        this property convert the data in this class to arguments netmiko.ConnectionHandler() can accept.
        example - netmiko.ConnectionHandler(**device.device_options).
        :return: a dictionary containing the arguments netmiko.ConnectionHandler() needs to run
        """
        json_dump = self.model_dump()
        del json_dump["name"]
        return json_dump


SUPPORTED_DEVICE_TYPES = [
    "cisco_ios",
    "cisco_ios_xe",
    "cisco_ios_telnet",
    "cisco_ios_xe_telnet"
]
