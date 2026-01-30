import logging
import math

from os import getcwd
from typing import Any
from json import dumps, load
from fastavro.schema import load_schema
from pystrm.kHandler.kProducer import Kprod
from pystrm.kHandler.kAdminstrator import KAdmin
from pystrm.kHandler.kSchemaRegistry import KSR
from pystrm.utils.common.constants import Constants


logger = logging.getLogger(__name__)

adm = KAdmin()

def createKtopic(topic: str, num_part: int = 1, replica: int = 1) -> None:

    adm.create_topic(topic=topic, num_part=num_part, replica=replica)   

    return None

def deleteKtopic(topic: str | list[str]) -> None:

    if isinstance(topic, str):
        topic = [topic]

    adm.delete_topic(topics=topic)   

    return None


def get_clientSchema(fl_nm: str, schema_type: str):

    path = Constants.INFRA_CFG.value["Kafka"]["schema"][schema_type.lower()]

    if schema_type == "JSON":
        fl_nm += ".json"
        with open(getcwd() + path + fl_nm) as fl:
            schema = load(fl)
    else:
        fl_nm += ".avsc"
        schema = load_schema(getcwd() + path + fl_nm)

    return schema


def registerClientSchema(topic: str, schema_type: str = "AVRO") -> None:

    schema_str = get_clientSchema(topic, schema_type=schema_type)
    schema_register = KSR(topic=topic, schema_str=dumps(schema_str), schema_type=schema_type)
    schema_register.register_schema()

    return None

def deregisterClientSchema(topic: str, schema_type: str = "AVRO") -> None:

    schema_str = get_clientSchema(topic, schema_type=schema_type)
    schema_register = KSR(topic=topic, schema_str=dumps(schema_str), schema_type=schema_type)
    schema_register.deregister_schema()

    return None


def handle_nan_values(data: dict[str, Any]) -> dict[str, Any]:
    """Convert NaN float values to None for serialization compatibility."""
    return {k: None if isinstance(v, float) and math.isnan(v) else v for k, v in data.items()}



def dataDupCheck(data_dct: dict[tuple[str, str], dict[str, Any]], typ: str, data: dict[str, Any], symb: str) -> bool:
    """Check if record is duplicate by comparing with previously stored data.
    
    Args:
        data_dct: Dictionary storing deduplicated records with (type, symbol) as key
        typ: Record type identifier
        data: Current record data
        symb: Stock symbol
        
    Returns:
        bool: True if record is new, False if duplicate
    """
    data_chk = data.copy()
    data_chk.pop(Constants.RECORD_TIMESTAMP_KEY.value, None)
    key = (typ, symb)
    
    if key in data_dct.keys():
        if data_dct[key] == data_chk:
            return False
        else:
            data_dct[key] = data_chk
            return True
    else:
        data_dct[key] = data_chk
        return True


async def validSend(kobj: Kprod, typ: str, data_dct: dict[tuple[str, str], dict[str, Any]], symb: str, data: dict[str, Any], schema_type: str, schema: object) -> None:
    """Validate and send data to Kafka if it's not a duplicate.
    
    Args:
        kobj: Kafka producer
        typ: Record type
        data_dct: Deduplication dictionary
        symb: Stock symbol
        data: Data to send
        schema_type: Schema type (json/avro)
        schema: Schema object for validation
    """
    if dataDupCheck(data_dct=data_dct, typ=typ, data=data, symb=symb):
        logger.info(f"New record found for symbol: {symb}")
        kobj.prodDataWithSerialSchema(schema=schema, data=data, mykey=symb, schema_type=schema_type)
    else:
        logger.info(f"Duplicate record skipped for symbol: {symb}")

    return None