import logging
import asyncio
import yfinance as yf

from time import sleep
from typing import Any
from numpy import long
from datetime import datetime
from zoneinfo import ZoneInfo

from pystrm.kHandler.kProducer import Kprod
from pystrm.kHandler.kUtils import handle_nan_values, validSend, get_clientSchema
from pystrm.utils.common.constants import Constants
from pystrm.utils.common.marketUtils import marketCheck
from pystrm.utils.logger.logDecor import logtimer, inOutLog

# # Force appdirs to use a different cache directory (e.g., '/tmp' or a local '.cache')
# CACHE_DIR = "/tmp" # Use an appropriate path that is writable by your user
# ad.user_cache_dir = lambda *args: CACHE_DIR

# # Create the cache directory if it doesn't exist
# Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)


logger = logging.getLogger(__name__)
local_tz = ZoneInfo("Asia/Kolkata")


async def asyncFastInfo(symb: str, meth: list[str]) -> dict[str, Any]:
    """Fetch fast info for a stock symbol using yfinance.
    
    Args:
        symb: Stock symbol (will append exchange suffix)
        meth: List of attribute names to fetch
        
    Returns:
        Dictionary with requested attributes and record timestamp
    """
    ct = datetime.now(local_tz)
    ticker_data = yf.Ticker(symb + Constants.STOCK_EXCHANGE_SUFFIX.value).fast_info
    
    # Use dict() instead of list conversion
    data = {
        k.lower(): v 
        for k, v in zip(meth, [ticker_data[item] for item in meth])
    }
    data[Constants.RECORD_TIMESTAMP_KEY.value] = long(ct.timestamp() * 1000)
    
    return handle_nan_values(data)


@inOutLog
async def ticks(kobj: Kprod, symbol: list[str], param_dct: dict[str, Any]) -> None:
    """Fetch ticker data from Yahoo Finance and produce to Kafka.

    Args:
        kobj: Kafka producer object
        symbol: List of stock symbols
        param_dct: Parameter dictionary with keys:
            - interval: Sleep interval between cycles
            - prop_key: Kafka topic
            - schema_type: Schema type (json/avro)
            - infolst: List of info attributes to fetch
            - type: 'Streaming' for continuous, else one-shot
    """
    handlers = {
        'fastinfo': asyncFastInfo
    }

    if param_dct['ldt'] not in handlers:
        logger.error(f"Unknown data type: {param_dct['ldt']}")
        return

    if not symbol:
        logger.info("Symbol list is empty")
        return
    
    interval: int = param_dct['interval']
    schema = get_clientSchema(param_dct['prop_key'], param_dct['schema_type'])
    dupCheck: dict[tuple[str, str], dict[str, Any]] = {}
    
    symbol_count = len(symbol)
    current_index = 0
    
    try:
        while True:
            current_index = current_index % symbol_count
            
            # Sleep and check market status only at cycle start
            if current_index == 0:
                sleep(interval)
                if not marketCheck():
                    logger.info("Market closed, stopping data fetch")
                    return
            
            try:
                current_symbol = symbol[current_index]
                data = await handlers[param_dct['ldt']](current_symbol, param_dct['infolst'])
                await validSend(
                    kobj, 
                    param_dct['ldt'], 
                    dupCheck, 
                    current_symbol, 
                    data, 
                    param_dct['schema_type'], 
                    schema
                )
            except Exception as e:
                logger.error(f"Error fetching data for {symbol[current_index]}: {e}")
            
            # Exit if not streaming mode and we've processed all symbols
            if param_dct['type'] != 'Streaming' and current_index == symbol_count - 1:
                break
            
            current_index += 1
                
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        return


@logtimer
def procHandler(param_dct: dict[str, Any], symb: list[str]) -> None:
    """Fetch data from Yahoo Finance and produce to Kafka.

    Args:
        param_dct: Parameter dictionary for execution
        symb: List of stock symbols for data fetch
    """
    kobj = Kprod(topic=param_dct['prop_key'])    
    
    asyncio.run(ticks(kobj, symb, param_dct))


        


