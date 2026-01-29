import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq, fsolve
from datetime import date, timedelta
from .commonfuns import nthwd, yy2yyyy, addmons
import polars as pl

def callprice_bs(S: float, K: float, T: float, r: float, q: float, sigma: float):
    '''
    Theoretical price of European call option using Black-Scholes model
    **Parameters**
    - S: spot price of underlying asset
    - K: strike price
    - T: time to maturity (in years)
    - r: risk-free interest rate (annualized)
    - q: dividend yield (annualized)
    - sigma: volatility of underlying asset (annualized)
    **Returns**: theoretical call option price
    **Example**
    callprice_bs(100, 105, 30/365, 0.03, 0.2)
    '''
    d1 = (np.log(S / K) + (r - q + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    cprc = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    res = (d1, d2, cprc)
    return res

class IndexOptions:
    def __init__(self):
        self.underlyings = {
            'csi300': 'IO',
            'csi1000': 'MO',
            'sse50': 'HO'
        }
        self.exercisetype = 'European'
        self.multiplier = 100
        self.listdates = {
            'csi300': date(2019, 12, 23),
            'csi1000': date(2022, 7, 22),
            'sse50': date(2022, 12, 19)
        }
    def contractcode(self, underlying: str, contractmon: str, call: bool, strike: int) -> str:
        '''
        Code for option with the given underlying, contract month and strike price
        **Parameters**
        - underlyting: underlying index, one of 'csi300', 'csi1000' or 'sse50'
        - contractmon: 'yymm', e.g. '2601'. According to cffex contract specifications, one of the following months: the current month, the next two months, and the subsequent three quarterly months of the Mar., Jun., Sep., and Dec. cycle
        - call: True for call option
        - strike: strike price
        **Returns**: contract code
        **Example**
        from cffex.indexoptions import IndexOptions as IOPT
        opt = IOPT()
        opt.contractcode('csi300', '2601', True, 4000)  # 'IO2601-C-4000
        '''
        assert underlying in self.underlyings.keys()       
        ocode = self.underlyings[underlying]
        contracttype = 'C' if call else 'P'
        return f'{ocode}{contractmon}-{contracttype}-{strike}'
    def lasttradingday(self, contractmon: str) -> date:
        '''
        Get the last trading day (3rd Friday of the contract's expiry month) 
        **Parameters**:
        - contractmon: contract month, e.g. '2601' 
        **Returns**: date
        **Example**
        from cffex.indexoptions import IndexOptions as IOPT
        opt = IOPT()
        opt.lasttradingday('2601')   # 2026-01-16 
        '''
        yy = int(contractmon[:2])
        m = int(contractmon[2:])
        return nthwd(yy2yyyy(yy), m, 3, 'fri')
    def contractmons(self, tradedate: str | date) -> tuple[str]:
        '''
        Tuple of contract months available on the given trading date
        **Parameters**
        - tradedate: date or datestring in 'yyyy-mm-dd' format
        **Return**: tuple of contract months in 'yymm' format
        **Example**
        from cffex.indexoptions import IndexOptions as IOPT
        opt = IOPT()
        d = date(2025, 12, 31)
        opt.contractmons(d)   # ('2601', '2602', '2603', '2606', '2609')
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
        # 2nd & 3rd contract: next 2 months
        ymd2 = addmons(date(y1, m1, 1), 1)
        ymd3 = addmons(date(y1, m1, 1), 2)
        y2 = ymd2.year
        m2 = ymd2.month
        y3 = ymd3.year
        m3 = ymd3.month
        # 4th contract: subsequent quarterly month after the 3rd contract
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
        y4 = y3 + qm_map[m3][0]
        m4 = qm_map[m3][1]
        # 5th contract: 3 months after the 4th contract
        ymd5 = addmons(date(y4, m4, 1), 3)
        y5 = ymd5.year
        m5 = ymd5.month
        yymms = tuple([f'{str(y)[-2:]}{m:02d}' for y, m in zip((y1, y2, y3, y4, y5), (m1, m2, m3, m4, m5))])
        return yymms
    def exercisedata(self, underlying: str, yr: int, mon: int) -> dict:
        '''
        Given underlying, year and month, get exercise data for options (call or put) of all strike prices
        **Parameters**
        - underlying: underlying index, one of 'csi300', 'csi1000' or 'sse50'
        - yr: year, e.g. 2025
        - mon: month, e.g. 1
        **Returns**: dict with keys 'oi' (open interest), 'vol_unexercised' (volume unexercised at expiration) and 'vol_exercised' (volume exercised)
        **Example**
        from cffex.indexoptions import IndexOptions as IOPT
        opt = IOPT()
        d_io2512 = opt.exercisedata('csi300', 2025, 12)
        # {'io':85082, 'vol_unexercised': 61096, 'vol_exercised': 23986}
        '''
        assert underlying in self.underlyings.keys()
        host = 'http://www.cffex.com.cn'
        col_map = {
            '期权月份': 'opt',
            '到期未平仓量': 'oi',
            '到期未行权量': 'vol_unexercised',
            '行权量': 'vol_exercised'
        }
        ocode = self.underlyings[underlying]
        yyyymm = f'{str(yr)}{mon:02d}'
        yymm = yyyymm[2:]
        url = f'{host}/sj/qqsj/xqcx/{yyyymm}/{yyyymm}_1.csv'
        # qqsj: 期权数据, xqcx: 行权查询
        res = pl.read_csv(url, encoding = 'gb2312').rename(
            col_map
        ).with_columns(
            pl.col('opt').str.strip_chars(' ')
        ).row(
            by_predicate = pl.col('opt') == f'{ocode}{yymm}',
            named = True
        )
        del res['opt']
        return res
    def impliedvolatility(self, tradedate: str | date, option_contract: str, prc_underlying: float, premium: float, rf: float, div_yld: float = 0.0) -> float:
        '''
        Get root of sigma from callprice_bs with Brent's method
        Objective function: theoretical price - market price
        **Parameters**
        - tradedate: date or datestring in 'yyyy-mm-dd' format
        - option_contract: option contract code, e.g. 'IO2601-C-4000'
        - prc_underlying: current price of underlying index
        - premium: current premium paid for the option
        - rf: risk-free rate
        - div_yld: dividend yield (annualized)
        **Returns**: implied volatility
        **Example**
        from cffex.indexoptions import IndexOptions as IOPT
        opt = IOPT()
        d = date(2025, 12, 31)   # tradedate
        opt_code = 'IO2601-C-4000'
        premium = 616.00
        sprc = 4629.94   # closing price of csi300 on 2025-12-31)
        rf = 0.016   # shibor-3m on 2025-12-31
        opt.impliedvolatility(d, opt_code, sprc, rf)
        '''
        assert option_contract.lower().find('-c-'), 'use call options!'
        expiration = self.lasttradingday(option_contract[2:6])
        strike = int(option_contract.split('-')[-1])
        if isinstance(tradedate, str):
            tradedate = date.fromisoformat(tradedate)
        T = (expiration - tradedate).days / 365
        try:
            iv = fsolve(
                lambda sigma: callprice_bs(prc_underlying, strike, T, rf, div_yld, sigma)[2] - premium,
                0.2
            )[0]
            return iv
        except ValueError:
            return np.nan
    def greeks(self, tradedate: str | date, option_contract: str, prc_underlying: float, premium: float, rf: float, div_yld: float = 0) -> dict:
        '''
        Greeks for call options
        **Parameters**
        - tradedate: date or datestring in 'yyyy-mm-dd' format
        - option_contract: option contract code, e.g. 'IO2601-C-4000'
        - prc_underlying: current price of underlying index
        - premium: current premium paid for the option
        - rf: risk-free rate
        **Returns**: dict with keys 'delta', 'gamma', 'vega' (volatility changes 1%), 'theta_daily' and 'rho' (rate changes 1%)
        **Example**
        from cffex.indexoptions import IndexOptions as IOPT
        opt = IOPT()
        d = date(2025, 12, 31)   # tradedate
        opt_code = 'IO2601-C-4000'
        premium = 616.00
        sprc = 4629.94   # closing price of csi300 on 2025-12-31)
        rf = 0.016   # shibor-3m on 2025-12-31
        opt.greeks(d, opt_code, sprc, rf)
        '''
        assert option_contract.lower().find('-c-'), 'use call options!'
        T = (self.lasttradingday(option_contract[2:6]) - tradedate).days / 365
        strike = int(option_contract.split('-')[-1])
        sigma = self.impliedvolatility(tradedate, option_contract, prc_underlying, premium, rf, div_yld)
        d1, d2, _ = callprice_bs(prc_underlying, strike, T, rf, div_yld, sigma)
        nd1_pdf = norm.pdf(d1)    
        delta = norm.cdf(d1)
        gamma = nd1_pdf / (prc_underlying * sigma * np.sqrt(T))
        vega = prc_underlying * np.sqrt(T) * nd1_pdf / 100   # volatility changes 1%
        theta = -(prc_underlying * nd1_pdf * sigma) / (2 * np.sqrt(T)) - rf * strike * np.exp(-rf * T) * norm.cdf(d2)
        theta_daily = theta / 365
        rho = strike * T * np.exp(-rf * T) * norm.cdf(d2) / 100  # rate changes 1%    
        res = {
            'delta': delta,
            'gamma': gamma,
            'vega': vega,
            'theta_daily': theta_daily,
            'rho': rho
        }
        return res
