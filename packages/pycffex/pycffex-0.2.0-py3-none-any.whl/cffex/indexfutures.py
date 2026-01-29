# index funtures in cffex

from datetime import date, timedelta
from .commonfuns import isleap, nthwd, addmons, yy2yyyy
from akshare import stock_zh_index_daily_em, futures_main_sina
import pandas as pd

class IndexFutures:
    def __init__(self, underlying: str = 'csi300'):
        assert underlying.lower() in ('csi300', 'csi500', 'csi1000', 'sse50'), 'underlying out of range'
        code_map = {
            'csi300': 'IF',
            'csi500': 'IC',
            'csi1000': 'IM',
            'sse50': 'IH'
        }
        listdate_map = {
            'csi300': date(2010, 4, 16),
            'csi500': date(2015, 4, 16),
            'csi1000': date(2022, 7, 22),
            'sse50': date(2015, 4, 16)
        }
        multiplier_map = {
            'csi300': 300,
            'csi500': 200,
            'csi1000': 200,
            'sse50': 300
        }
        self.underlying = underlying.lower()
        self.multiplier = multiplier_map[underlying.lower()]
        self.code = code_map[underlying.lower()]
        self.listdate = listdate_map[underlying.lower()]      
    def lasttradingday(self, contractmon: str) -> date:
        '''
        Get the last trading day (3rd Friday of the contract's expiry month) 
        **Parameters**:
        - contractmon: contract month, e.g. '2601' 
        **Returns**: date
        **Example**
        from cffex.indexfutures import IndexFutures as IFut
        fut300 = IFut('csi300')
        fut300.lasttradingday('2601')   # 2026-01-16 
        '''
        yy = int(contractmon[:2])
        m = int(contractmon[2:])
        return nthwd(yy2yyyy(yy), m, 3, 'fri')
    def getcontracts(self, tradedate: str | date) -> tuple[str]:
        '''
        Contracts available on the given trading date
        **Parameters**
        - tradedate: date
        **Return**: tuple of contract codes
        **Example**
        from cffex.indexfutures import IndexFutures as IFut
        fut300 = IFut()
        d = date(2025, 12, 17)
        fut300.getcontracts(d)   # ('IF2512', 'IF2601', 'IF2603', 'IF2606')
        '''
        if isinstance(tradedate, str):
            tradedate = date.fromisoformat(tradedate)    
        # 1st contract: current month
        y1 = tradedate.year
        m1 = tradedate.month
        if tradedate > nthwd(y1, m1, 3, 'fri'):
            if m1 == 12:
                y1 += 1
                m1 = 1
            else:
                m1 += 1
        # 2nd contract: next month
        ymd2 = addmons(date(y1, m1, 1), 1)
        y2 = ymd2.year
        m2 = ymd2.month
        # 3rd contract: subsequent quarterly month after 2nd contract
        qm_map = {
            1: (0, 3),   # year plus 0, quarterly month is Mar. 
            2: (0, 3),
            3: (0, 6),
            4: (0, 6),
            5: (0, 6),
            6: (0, 9),
            7: (0, 9),
            8: (0, 9),
            9: (0, 12),
            10: (0, 12),
            11: (0, 12),
            12: (1, 3)
        }
        y3 = y2 + qm_map[m2][0]
        m3 = qm_map[m2][1]
        # 4th contract: 3 months after year and month of 3rd contract
        ymd4 = addmons(date(y3, m3, 1), 3)
        y4 = ymd4.year
        m4 = ymd4.month
        contracts = tuple([f'{self.code}{str(y)[-2:]}{m:02d}' for y, m in zip((y1, y2, y3, y4), (m1, m2, m3, m4))])
        return contracts
    def spothist(self, startdate: str | date, enddate: str | date) -> pd.DataFrame:
        '''
        Retrieving historical trading data from eastmoney with akshare for the underlying index
        **Parameters**
        - startdate: start date
        - enddate: end date
        **Returns**: pandas.DataFrame
        **Example**
        from cffex.indexfutures import IndexFutures as IFut
        fut300 = IFut()
        hist_csi300 = fut300.spothist('2025-12-01', '2025-12-31')
        '''
        if isinstance(startdate, str):
            startdate = date.fromisoformat(startdate)
        if isinstance(enddate, str):
            enddate = date.fromisoformat(enddate)
        startdate = startdate.strftime('%Y%m%d')
        enddate = enddate.strftime('%Y%m%d')
        idxcode_map = {
            'csi300': 'sh000300',
            'csi500': 'sh000905',
            'csi1000': 'sh000852',
            'sse50': 'sh000016'
        }
        col_map = {
            'open': 'openprice',
            'high': 'highprice',
            'low': 'lowprice',
            'close': 'closeprice'
        }
        df = stock_zh_index_daily_em(
            symbol = idxcode_map[self.underlying],
            start_date = startdate,
            end_date = enddate
        )
        df.rename(columns = col_map, inplace = True)
        return df
    def futhist(self, startdate: str | date, enddate: str | date) -> pd.DataFrame:
        '''
        Retrieving historical trading data from sina with akshare for continuous contract (主力连续合约)
        **Parameters**
        - startdate: start date
        - enddate: end date
        **Returns**: pandas.DataFrame
        **Example**
        from cffex.indexfutures import IndexFutures as IFut
        fut300 = IFut()
        hist_if0 = fut300.futhist('2025-12-01', '2025-12-31')
        '''
        if isinstance(startdate, str):
            startdate = date.fromisoformat(startdate)
        if isinstance(enddate, str):
            enddate = date.fromisoformat(enddate)
        startdate = startdate.strftime('%Y%m%d')
        enddate = enddate.strftime('%Y%m%d')
        df = futures_main_sina(
            symbol = self.code + '0',
            start_date = startdate,
            end_date = enddate
        )
        col_map = {
            '日期': 'date',
            '开盘价': 'openprice',
            '最高价': 'highprice',
            '最低价': 'lowprice',
            '收盘价': 'closeprice',
            '成交量': 'volume',
            '持仓量': 'openinterest'
        }
        df.rename(columns = col_map, inplace = True)
        return df[['date', 'openprice', 'highprice', 'lowprice', 'closeprice', 'volume', 'openinterest']]
        