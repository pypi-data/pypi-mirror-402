import os
import sys
import logging
import logging.config
import tomllib

from pprint import pformat
from typing import Any
from datetime import datetime
from pathlib import Path
from multiprocessing_logging import install_mp_handler


def main_function(mthd: str, conf_key: str, path: str = os.getcwd()) -> None: 

    # Get the directory of the currently running script/module
    script_dir = Path(__file__).resolve().parent
    toml_file_path = script_dir / "pyproject.toml"

    if toml_file_path.exists():
        try:
            with open(toml_file_path, "rb") as f:
                toml_dtl = tomllib.load(f)
            print("Successfully loaded pyproject.toml")
            # print(data) # Uncomment to see the content
        except Exception as e:
            print(f"Error reading file: {e}")
            raise e
    else:
        print(f"Error: pyproject.toml not found at {toml_file_path}")
        raise FileNotFoundError(f'{toml_file_path} does not exist')

    if not os.path.exists(path):
        raise FileNotFoundError(f'{path} does not exist')

    os.chdir(path)

    from pystrm.utils.common.constants import Constants

    if 'Logging' in Constants.INFRA_CFG.value.keys():

        from pystrm.utils.common.confs import update_utils_values

        config: dict[str, Any] = Constants.INFRA_CFG.value['Logging']

        update_utils_values(config, toml_dtl['project']['name'])

        if 'file_json' in config['handlers']:
            Path(Path.cwd()/'logs').mkdir(exist_ok=True)
            config['handlers']['file_json']['filename'] += datetime.now().strftime('%Y-%m-%d.json')

        logging.config.dictConfig(config)
        
    logger = logging.getLogger()

    install_mp_handler(logger)
    
    logger.info("Intitiating program with run_id : " + str(Constants.RUN_ID.value))

    from pystrm.mainCalls.yfUtils import getLiveTickData

    __method_to_excute = {
        "liveYfinanaceTick": getLiveTickData
    }
    
    try:

        if mthd not in __method_to_excute.keys():
            msg = "List of operation mentioned in dictionary for this package"
            raise KeyError
        else:
            logger.info(f"Operation {mthd} exists. Validating other input")
        
        if (conf_key.split('.')[0] not in Constants.TBL_CFG.value.keys()) or (conf_key.split('.')[1] not in Constants.TBL_CFG.value[conf_key.split('.')[0]]):
            msg = f"key:{conf_key.split('.')[0]} and value: {conf_key.split('.')[1]} pair does not exists in tables.yml"
            raise KeyError
        else:
            logger.info(f"Configuration found in tables.yml for {conf_key}")
            logger.info("Config found for this operation from tables.yml are as below:")
            logger.info(f"\n{pformat(Constants.TBL_CFG.value[conf_key.split('.')[0]], indent=4)}")

        return __method_to_excute[mthd](conf_key)
    except TypeError:
        logger.critical(f"main() function takes exactly 2 arguments ({len(sys.argv[1:])} given)")
        raise TypeError
    except KeyError:
        logger.critical(f'Key not found: {msg}')
        raise KeyError
    except Exception as e:
        logger.critical("Error occur while initiating: " + str(e))
        raise e


if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()

    parser.add_argument("-m", "--method", type=str, help="Method to execute", required=True)
    parser.add_argument("-k", "--key", type=str, help="Key required for properties", required=True)
    parser.add_argument("-c", "--cfg_path", type=str, help="Config path of config files", required=False, default=os.getcwd())

    args = parser.parse_args()

    if hasattr(args, 'cfg_path'):
        main_function(args.method, args.key, args.cfg_path)
    else:
        main_function(args.method, args.key)
