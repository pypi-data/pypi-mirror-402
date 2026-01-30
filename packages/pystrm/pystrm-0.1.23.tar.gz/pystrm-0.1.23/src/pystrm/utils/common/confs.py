import logging

from typing import Any
from yaml import safe_load

logger = logging.getLogger(__name__)

def fetch_prop() -> dict[str, Any]:
    try:
        with open('tables.yml', 'r') as tblinfo:
            prop_dict = safe_load(tblinfo.read())
    except Exception as e:
        logger.critical(f"Error occured for config file 'tables.yaml' : {str(e)}")
        raise e

    return prop_dict


def fetch_conf() -> dict[str, Any]:
    try:
        with open('config.yml', 'r') as cfginfo:
            conf_dict = safe_load(cfginfo.read())
    except Exception as e:
        logger.critical(f"Error occured for config file 'config.yaml' : {str(e)}")
        raise e
        
    return conf_dict

def update(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def update_utils_values(d: dict[str, Any], new_add: str) -> None:
    """
    Recursively update all values in nested dictionary where values start with 'utils.'.
    
    Args:
        d: The nested dictionary to update
        new_value: The new value to set for matching values
    """
    for k, v in d.items():
        if isinstance(v, str) and v.startswith("utils."):
            d[k] = new_add + "." + v
        elif isinstance(v, dict):
            update_utils_values(v, new_add)
