from typing import Optional
from pydantic import BaseModel


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
        return ssh_string

    @property
    def device_options(self):
        json_dump = self.model_dump()
        del json_dump["name"]
        return json_dump


SUPPORTED_DEVICE_TYPES = [
    "cisco_ios",
    "cisco_ios_xe",
    "cisco_ios_telnet",
    "cisco_ios_xe_telnet"
]
