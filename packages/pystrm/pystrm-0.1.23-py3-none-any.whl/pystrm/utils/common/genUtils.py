
from typing import Any
from pystrm.utils.common.marketUtils import nifty50
from pystrm.utils.common.constants import Constants


def param_init(key: str) -> Any:

    conf_key = key.split('.')[0]
    prop_key = key.split('.')[1]
    conf_dict = Constants.INFRA_CFG.value[conf_key]
    prop_dict = Constants.TBL_CFG.value[conf_key][prop_key]

    return prop_key, conf_dict, prop_dict


def fetch_db_dtl(db_type: str) -> dict[str, str | int]:
    db_dtl = Constants.INFRA_CFG.value[db_type]
    return db_dtl


def streamConf(key: str) -> tuple[int, int, list[str], dict[str, Any]]:

    prop_key, conf_dict, prop_dict = param_init(key) 
    symbols: list[str] = list(set(nifty50() + Constants.INFRA_CFG.value['Market']['Symbols']))
    
    prop_dict['prop_key'] = prop_key.lower()
    prop_dict['interval'] = Constants.INFRA_CFG.value['Market']['Interval']

    num_proc: int = int(conf_dict['num_process'])

    num_process: int = len(symbols)//num_proc

    if len(symbols) % num_proc == 0:
        num_proc = num_proc
    else:
        num_proc = num_proc + 1
    
    return (num_proc, num_process, symbols, prop_dict)




'''@logtimer
@staticmethod
def niftySymbols(url: str) -> list[str]:
    
    session = requests.Session()
    r = session.get(BASE_URL, headers=HEADERS, timeout=5)
    cookies = dict(r.cookies)
    
    response = session.get(url, timeout=5, headers=HEADERS, cookies=cookies)
    content = response.content.decode('utf-8')

    columns=['Company Name', 'Industry', 'Symbol', 'Series', 'ISIN Code']
    data_lst = [x.strip().split(',') for x in content.splitlines() if x.strip().split(',') != columns]              

    df=pd.DataFrame(data_lst, columns=columns)
    symbols_lst = df['Symbol'].tolist()
    
    return symbols_lst'''
