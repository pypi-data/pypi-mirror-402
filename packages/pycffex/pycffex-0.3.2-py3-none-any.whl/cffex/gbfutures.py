# gb futures in cffex

from datetime import date, timedelta
from fixedratebond import FRB
from cnexchcal import ExchCal as CNC
from .commonfuns import addmons, nthwd, yy2yyyy, isleap
from akshare import futures_main_sina
import pandas as pd

class GBFutures:
    def __init__(self, tenor: int = 5):
        code_map = {2: "TS", 5: "TF", 10: "T", 30: "TL"}
        listdate_map = {
            2: date(2017, 2, 27),
            5: date(2013, 9, 6),
            10: date(2015, 3, 20),
            30: date(2023, 4, 21)
        }
        assert tenor in code_map, f'{tenor} is not a valid tenor for gbf contract.'
        self.tenor = tenor
        self.code = code_map[tenor]
        self.listdate = listdate_map[tenor]
    def lasttradingday(self, contractmon: str) -> date:
        '''
        Get the last trading day (2nd Friday of the contract's expiry month) 
        Parameters:
        - contractmon: contract month, e.g. '2603' 
        Returns: date
        Example:
        from cffex.gbfutures import GBFutures as GBF
        gbf = GBF(10)
        gbf.lasttradingday('2603')   # 2026-03-17     
        '''
        yy = int(contractmon[:2])
        m = int(contractmon[2:])
        return nthwd(yy2yyyy(yy), m, 2, 'fri')
    def getcontracts(self, tradedate: date) -> tuple[str]:
        '''
        contracts available on the given trading date
        Parameters:
        - tradedate: date
        Return: tuple
        Example:
        from cffex.gbfutures import GBFutures as GBF
        gbf = GBF(10)
        gbf.getcontracts(date(2025, 12, 17))   # ('T2603', 'T2606', 'T2609')
        '''    
        # nearest quaterly year-month for specified month (if the last trading day has passed, use next month)
        # e.g. trading date: 2025-12-17, last trading day for TF2512: 2025-12-12 (2nd Friday of Dec)
        # the specified month is 1 (Jan), year of contract is 2026 (2025 + 1)
        qm1_map = {
            1: (0, 3), # year plus 0, quarterly month is Mar.
            2: (0, 3),
            3: (0, 3),
            4: (0, 6),
            5: (0, 6),
            6: (0, 6),
            7: (0, 9),
            8: (0, 9),
            9: (0, 9),
            10: (0, 12),
            11: (0, 12),
            12: (0, 12)
        }
        # year & month for 1st contract
        y_cur = tradedate.year
        m_cur = tradedate.month
        if tradedate > nthwd(y_cur, m_cur, 2, 'fri'):
            if m_cur == 12: 
                y_cur += 1
                m_cur = 1
            else:
                m_cur += 1
        y1 = y_cur + qm1_map[m_cur][0]
        m1 = qm1_map[m_cur][1]
        # year & month for the 2nd contract
        ymd2 = addmons(date(y1, m1, 1), 3)
        y2 = ymd2.year
        m2 = ymd2.month
        # year & month for the 3rd contract
        ymd3 = addmons(date(y1, m1, 1), 6)
        y3 = ymd3.year
        m3 = ymd3.month
        contracts = tuple([f'{self.code}{str(y)[-2:]}{m:02d}' for y, m in zip((y1, y2, y3), (m1, m2, m3))])
        return contracts
    def deliverable(self, contractmon: str, bond: FRB) -> bool:
        '''
        is the bond deliverable for the futures contract? take acount of tenor ONLY
        Parameters:
        - contractmon: str, futures contract yearmonth, e.g. "2603"
        - bond: FRB, object of a fixed rate bond
        Return: bool
        Example
        from cffex.gbfutures import GBFutures as GBF
        from fixedratebond import FRB
        gbf = GBF(5)
        b = FRB(date(2030, 6, 25), 0.0262, 1)   # 23附息国债14
        gbf.deliverable('2603', b)   # True
        '''
        d = date(yy2yyyy(int(contractmon[:2])), int(contractmon[2:]), 1)
        yr = bond.yearsresidual(d)
        rule1 = {2: 5, 5: 7, 10: 10, 30: 30}   # initial tenor
        rule2 = {2: (1.5, 2.25), 5: (4, 5.25), 10: (6.5, None), 30: (25, None)}   # residual tenor on 1st trading day in expiration month
        if bond.issuedate is None:
            r2 = rule2[self.tenor]
            if r2[1] is None:
                return yr >= r2[0]
            else:
                return r2[0] <= yr <= r2[1]
        else:
            yriss = bond.yearsresidual(bond.issuedate)
            r1 = rule1[self.tenor]
            r2 = rule2[self.tenor]
            if r2[1] is None:
                return (yriss <= r1) and (yr >= r2[0])
            else:
                return (yriss <= r1) and (r2[0] <= yr <= r2[1])
    def conversionfactor(self, contractmon: str, bond: FRB) -> float:
        '''
        conversion factor for a given deliverable bond
        Parameters:
        - contractmon: str, futures contract yearmonth, e.g. "2603"
        - bond: FRB, object of a fixed rate bond
        Return: float ('.4f')
        Example
        from cffex.gbfutures import GBFutures as GBF
        from fixedratebond import FRB
        gbf = GBFutures(5)
        b = FRB(date(2030, 6, 25), 0.0262, 1)   # 23附息国债14
        gbf.conversionfactor('2603', b)   # 0.985
        '''
        assert self.deliverable(contractmon, bond), 'NOT a deliverable bond'
        r = 0.03   # nominal coupon rate of underlying
        d = CNC().next_nth_tradingday(self.lasttradingday(contractmon), 2)
        ncd = bond.coupncd(d)
        y0 = yy2yyyy(int(contractmon[:2]))
        m0 = int(contractmon[2:])        
        y1 = ncd.year
        m1 = ncd.month
        x = (y1 - y0) * 12 + m1 - m0   # months from contract month to next coupon payment date
        n = bond.coupnum(d)
        c = bond.couponrate
        f = bond.frequency
        cf = 1 / ((1 + r/f) ** (x * f / 12)) * (c / f + c / r + (1 - c / r) / ((1 + r / f) ** (n - 1))) - c / f * (1 - x * f / 12)
        return round(cf, 4)    
    def invoiceprice(self, contractmon: str, bond: FRB, settlementprice: float, deliverydate: date = None) -> float:
        '''
        invoice price for delivery
        Parameters
        - contractmon: str, futures contract yearmonth, e.g. "2603"
        - bond: FRB, object of a fixed rate bond
        - settlementprice: float, settlement price of the futures
        - deliverydate: date, delivery date, if None, use the 2nd delivery day
        Return: float. how many decimal places? cffex does not specify. settlement price: 3; accrued interest: 7; conversion factor: 4
        So we use '.4f' here
        Example
        from cffex.gbfutures import GBFutures as GBF
        from fixedratebond import FRB
        gbf = GBFutures(5)
        b = FRB(date(2030, 6, 25), 0.0262, 1)
        gbf.invoiceprice('2603', b, 104.735)
        '''
        if deliverydate is None:
            deliverydate = CNC().next_nth_tradingday(self.lasttradingday(contractmon), 2)
        ai = bond.accrint(deliverydate)
        cf = self.conversionfactor(contractmon, bond)
        invoice = settlementprice * cf + ai
        return round(invoice, 4)
    def irr(self, contractmon: str, bond: FRB, tradedate: date, spotprice: float, futprice: float, deliverydate: date = None) -> float:
        '''
        implied repo rate for a given deliverable bond
        Parameters:
        - contractmon: str, futures contract yearmonth, e.g. "2603"
        - bond: FRB, object of a fixed rate bond
        - tradedate: date, trading date to buy bond and create futures short position
        - spotprice: float, clean price the bond bought
        - futprice: float, settlement price of the futures on tradedate
        - deliverydate: date, delivery date, if None, use the 2nd delivery day
        Return: float
        Example
        from cffex.gbfutures import GBFutures as GBF
        from fixedratebond import FRB
        gbf = GBF(5)
        b = FRB(date(2030, 6, 25), 0.0226, 1)
        gbf.irr('2603', b, date(2025, 12, 12), 104.45, 105.82)
        '''
        if deliverydate is None:
            deliverydate = CNC().next_nth_tradingday(self.lasttradingday(contractmon), 2)
        ai0 = bond.accrint(tradedate)
        ai1 = bond.accrint(deliverydate)
        cf = self.conversionfactor(contractmon, bond)
        v0 = spotprice + ai0
        v1 = cf * futprice + ai1
        n = (deliverydate - tradedate).days
        return (v1 / v0 - 1) * 365 / n
    def futhist(self, startdate: str | date, enddate: str | date) -> pd.DataFrame:
        '''
        historical data of main contract (主力连续合约) from sina with akshare
        Parameters:
        - startdate: start date, date or date string ('yyyy-mm-dd')
        - enddate: end date, date or date string ('yyyy-mm-dd')
        Return: pd.DataFrame
        Example
        from cffex.gbfutures import GBFutures as GBF
        gbf = GBF(5)
        gbf.futhist('2025-12-01', '2025-12-19')
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
