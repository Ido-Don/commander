from typing import Optional
from pydantic import BaseModel

MAIN_GROUP_NAME = "device"


class Device(BaseModel):
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
        ssh_string = ""
        if self.username:
            ssh_string += f"{self.username}@"
        ssh_string += self.host
        if self.port:
            ssh_string += f":{self.port}"

    @property
    def device_options(self):
        _device_options = {
            "username": self.username,
            "password": self.password,
            "host": self.host,
            "device_type": self.device_type
        }
        if self.port:
            _device_options["port"] = self.port
        return _device_options


