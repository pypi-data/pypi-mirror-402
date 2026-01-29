import configparser
import os
from typing import Any, Optional


from artefacts.cli.constants import CONFIG_PATH, CONFIG_DIR
from artefacts.cli.errors import InvalidAPIKey


def is_valid_api_key(value: Any) -> bool:
    """
    Valid means non-empty string object.
    """
    try:
        return value and len(value) > 0
    except TypeError:
        return False


def get_conf_from_file():
    config = configparser.ConfigParser()
    if not os.path.isfile(CONFIG_PATH):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config["DEFAULT"] = {}
        with open(CONFIG_PATH, "w") as f:
            config.write(f)
    config.read(CONFIG_PATH)
    return config


def set_global_property(key: str, value: Any) -> None:
    config = get_conf_from_file()
    config.set("global", key, value)
    with open(CONFIG_PATH, "w") as f:
        config.write(f)


def get_global_property(key: str, default: Optional[Any] = None) -> Optional[Any]:
    config = get_conf_from_file()
    return config.get("global", key, fallback=default)


def add_key_to_conf(project_name: str, api_key: str) -> None:
    """
    Add a valid key to the configuration file.
    """
    if is_valid_api_key(api_key):
        config = get_conf_from_file()
        config[project_name] = {"ApiKey": api_key}
        with open(CONFIG_PATH, "w") as f:
            config.write(f)
    else:
        raise InvalidAPIKey()
