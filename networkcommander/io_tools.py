import yaml


def convert_to_yaml(content: str):
    new_yaml = yaml.safe_load(content)
    return new_yaml
