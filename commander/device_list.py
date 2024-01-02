from device import get_all_devices, KeepassDB


def get_device_list(keepass_db_path: str) -> str:
    with KeepassDB(keepass_db_path) as kp:
        devices = get_all_devices(kp)

    formatted_device_list = format_device_list(devices)
    return formatted_device_list


def format_device_list(devices):
    output = ""
    for device_name, device_options in devices.items():
        username = device_options["username"]
        port = device_options["port"]
        host = device_options["host"]
        device_type = device_options["device_type"]
        device_string = f"{device_name}({device_type}) -> "
        device_string += ssh_string(host, port, username)
        device_string += '\n'
        output += device_string
    return output


def ssh_string(host, port, username):
    device_string = ''
    if username:
        device_string += f"{username}@"
    device_string += host
    if port:
        device_string += f":{port}"
    return device_string
