import os
import logging
from multiprocessing import Pool
from pystrm.stream.yfStream.ticksStream import procHandler
from pystrm.kHandler.kUtils import createKtopic, registerClientSchema
from pystrm.utils.common.genUtils import streamConf
from pystrm.utils.common.marketUtils import mliveduration
from pystrm.utils.logger.logDecor import inOutLog, process_status

logger = logging.getLogger(__name__)


@inOutLog
def getLiveTickData(key: str) -> None:
    """Generate data from NSE

    Args:
        key (str): Take config key as input
    """

    mtimeout = mliveduration()

    num_proc, num_process, symbols, prop_dict = streamConf(key)

    createKtopic(topic=prop_dict['prop_key'], num_part=9, replica=3)

    if 'schema_type' in prop_dict.keys():
        registerClientSchema(topic=prop_dict['prop_key'], schema_type=prop_dict['schema_type'])

    try:
        pool = Pool(processes=os.cpu_count())

        input_list = list()
        for i in range(1, num_proc+1):
            if i == num_proc:
                input_list.append((prop_dict, symbols[(i - 1)*num_process:]))
            else:
                input_list.append((prop_dict, symbols[(i-1)*num_process:i*num_process]))
            
        ar = pool.starmap_async(procHandler, input_list, error_callback=process_status)
        ar.wait(timeout=mtimeout + 300)
        if ar.ready():
            logger.info("All task finished")
        else:
            logger.error("Some task still running")
            pool.terminate()
            return None
    except KeyboardInterrupt as e:
        logger.warning("Keyboard Interrupt : " + str(e))
        pool.terminate()
        return None
    except Exception as e:
        logger.error(str(e))
        pool.terminate()
        return None