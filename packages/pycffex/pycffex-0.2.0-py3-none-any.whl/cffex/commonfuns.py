from datetime import date, timedelta

def yy2yyyy(yy: int, crit: int = 69) -> int:
    '''
    convert 2-digit year to 4-digit year
    crit: critical value, yy >= crit, 19yy; else: 20yy
    '''
    return 1900 + yy if yy >= crit else 2000 + yy

def isleap(yyyy: int) -> bool:
    return (yyyy % 4 == 0 and yyyy % 100 != 0) or yyyy % 400 == 0

def nthwd(yr: int, mo: int, n: int, wd: str) -> date:
    '''
    nth occurrence of weekday in a given year and month
        
    parameters:
    - yr: year
    - mo: month
    - n: nth occurrence
    - wd: weekday ('Sun', 'Mon', ..., 'Sat')
    
    return: date
    '''
    wds = {'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5}
    d1 = date(yr, mo, 1)
    wd_int = wds[wd.lower()]
    ds_ahead = (wd_int - d1.weekday() + 7) % 7
    res = d1 + timedelta(days = ds_ahead + (n - 1) * 7)
    if res.month != mo:
        raise ValueError(f'The {n}th {wd} does not exist in this month')
    return res

def addmons(d: date, n: int) -> date:
    '''
    add n (postive or negative) months to a given date
    
    parameters:
    - d: original date
    - n: number of months to add
    
    return: date
    '''
    y0 = d.year
    m0 = d.month
    d0 = d.day
    m1 = (m0 + n - 1) % 12 + 1
    y1 = y0 + (m0 + n - 1) // 12
    day_max = [
        31, 28 + isleap(y1), 31, 30, 31, 30, \
        31, 31, 30, 31, 30, 31
    ]
    d1 = min(d0, day_max[m1 - 1])
    return date(y1, m1, d1) 
