# fixed-rate bond
# method names mimic to MS Excel

import datetime
from numpy import exp
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('cnfixedratebond')
except PackageNotFoundError:
    __version__ = 'unknown'

__doc__ = '''
Compulation on Fixed Rate Bond in China
- market: ib, sse, szse
- method: yearresidual, price, ...
'''

def isleap(yr: int) -> bool:
    '''
    is yr a leap year?
    param yr: yyyy
    return: bool
    '''
    return (yr % 4 == 0 and yr % 100 != 0) or (yr % 400 == 0)

def includeleapday(d1: datetime.date, d2:datetime.date, *, closed: str = 'both') -> bool:
    '''
    if there is leap day (Feb 29) between d1 and d2
    param:
        - d1: start date
        - d2: end date
        - closed: 'both', 'left', 'right', 'neither'
    return: bool
    '''
    adj = {
        'both': (0, 0),
        'left': (0, -1),
        'right': (-1, 0),
        'neither': (-1, -1)
    }
    d1 += datetime.timedelta(days = adj[closed][0])
    d2 += datetime.timedelta(days = adj[closed][1])
    i = 0
    while (d := d1 + datetime.timedelta(days = i)) <= d2:
        if d.month == 2 and d.day == 29:
            return True
        i += 1
    return False
        
def addmons(d: datetime.date, n: int) -> datetime.date:
    '''
    add n months to d
    param:
        - d: start date
        - n: number of months to add    
    '''
    d_max = (31, 28 + isleap(d.year), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    y = d.year + (d.month + n - 1) // 12
    m = (d.month + n - 1) % 12 + 1
    d = min(d.day, d_max[m - 1])
    return datetime.date(y, m, d)

class FRB:
    def __init__(self, maturity: datetime.date, rate: float, freq: int, issuedate: datetime.date = None):
        self.maturitydate = maturity
        self.couponrate = rate
        self.frequency = freq
        self.issuedate = issuedate
    def yearsresidual(self, settlement: datetime.date) -> float:
        '''
        Residual maturity from settlement date to maturity date in years
        **param**
            - settlement: settlement date
        **Return**: float
        **Example**
        from fixedratebond import FRB
        from datetime import date
        # basic info: 25国债22
        maturity = date(2035, 11, 15)
        coupon = 0.0178
        freq = 2
        b = FRB(maturity, coupon, freq)
        d = date.today()
        b.yearsresidual(d)
        '''
        # actual days between settlementdate and maturitydate
        ds = (self.maturitydate - settlement).days
        # average days per year
        y1 = settlement.year
        y2 = self.maturitydate.year
        ly = [isleap(y) for y in range(y1, y2 + 1)]
        davg = 365 + sum(ly) / len(ly)
        return round(ds / davg, 4)
    def coupnum(self, settlement: datetime.date) -> int:
        '''
        Number of coupon payments from settlement date to maturity date
        **Parameters**
        - settlement: settlement date
        **Return**: int
        **Example**
        from fixedratebond import FRB
        from datetime import date
        # basic info: 25国债22
        maturity = date(2035, 11, 15)
        coupon = 0.0178
        freq = 2
        b = FRB(maturity, coupon, freq)
        d = date.today()
        b.coupnum(d)
        '''
        n = int(self.yearsresidual(settlement) * self.frequency)
        # NB: n * 12 / self.frequency returns a float, not an int
        if addmons(self.maturitydate, -n * 12 // self.frequency) > settlement:
            n += 1
        if addmons(self.maturitydate, -(n - 1) * 12 // self.frequency) < settlement:
            n -= 1
        return n
    def couppcd(self, settlement: datetime.date) -> datetime.date:
        '''
        Previous coupon payment date
        **Parameters**
        - settlement: settlement date
        **Return**: date
        **Example**
        from fixedratebond import FRB
        from datetime import date
        # basic info: 25国债22
        maturity = date(2035, 11, 15)
        coupon = 0.0178
        freq = 2
        b = FRB(maturity, coupon, freq)
        d = date.today()
        b.couppcd(d)
        '''
        n = self.coupnum(settlement)
        return addmons(self.maturitydate, -n * 12 // self.frequency)
    def coupncd(self, settlement: datetime.date) -> datetime.date:
        '''
        Next coupon payment date
        **Parameters**
        - settlement: settlement date
        **Return**: date
        **Example**
        from fixedratebond import FRB
        from datetime import date
        # basic info: 25国债22
        maturity = date(2035, 11, 15)
        coupon = 0.0178
        freq = 2
        b = FRB(maturity, coupon, freq)
        d = date.today()
        b.coupncd(d)
        '''
        n = self.coupnum(settlement)
        return addmons(self.maturitydate, -(n - 1) * 12 // self.frequency)
    def accrint(self, settlement: datetime.date, *, dcc: str = 'act/act') -> float:
        '''
        Accrued interest from previous coupon payment date to settlement date
        **Parameters**
        - settlement: settlement date
        - dcc: kwarg, day count convention, "act/act", "act/365", "nl/365", ...
        **Return**: float
        **Example**
        from fixedratebond import FRB
        from datetime import date
        # basic info: 25国债22
        maturity = date(2035, 11, 15)
        coupon = 0.0178
        freq = 2
        b = FRB(maturity, coupon, freq)
        d = date.today()
        b.accrint(d)
        b.accrint(d, dcc = 'szse')
        '''
        dcc = dcc.lower()
        pcd = self.couppcd(settlement)
        ncd = self.coupncd(settlement)
        if dcc in ("act/act", "actual/actual", "ib"):
            ai = (settlement - pcd).days / (ncd - pcd).days * self.couponrate * 100 / self.frequency
        elif dcc in ("act/365", "actual/365", "sh", "sse", "shanghai"):
            ai = (settlement - pcd).days / 365 * self.couponrate * 100
        elif dcc in ("nl/365", "sz", "szse", "shenzhen"):
            ai = ((settlement - pcd).days - includeleapday(pcd, settlement)) / 365 * self.couponrate * 100
        else:
            raise ValueError("dcc not available")
        return ai
    def __cfs(self, settlement: datetime.date) -> tuple[list[datetime.date], list[float], list[float]]:
        '''
        Private method, cash flows for a frb
        **Parameters**
        - settlement: settlement date
        **Return**
        tuple of lists:
            - payment dates
            - periods from settlement date to each coupon payment date
            - cash flows paid
        '''
        n = self.coupnum(settlement)
        pcd = self.couppcd(settlement)
        ncd = self.coupncd(settlement)
        # periods from settlement date to ncd
        a = (ncd - settlement).days / (ncd - pcd).days
        paydate = [addmons(self.maturitydate, -(n - t) * 12 // self.frequency) for t in range(1, n + 1)]
        t = [a + i for i in range(n)]
        cf = [self.couponrate * 100 / self.frequency] * n
        cf[n - 1] += 100
        return (paydate, t, cf)
    def price(self, settlement: datetime.date, yld: float, *, dcc: str = 'act/act') -> float:
        '''
        Theoretical clean price, i.e. intrinsic value
        **Parameters**
        - settlement: settlement date
        - yld: discount rate, or theoretical yield
        **Return**: float
        **Example**
        from fixedratebond import FRB
        from datetime import date
        # basic info: 25国债22
        maturity = date(2035, 11, 15)
        coupon = 0.0178
        freq = 2
        b = FRB(maturity, coupon, freq)
        d = date.today()
        b.price(d, 0.05)
        b.price(d, 0.05, dcc = 'szse')
        '''
        y = yld / self.frequency
        i = self.couponrate / self.frequency
        n = self.coupnum(settlement)
        pcd = self.couppcd(settlement)
        ncd = self.coupncd(settlement)
        a = (ncd - settlement).days / (ncd - pcd).days
        dirty = (100 * i * (1 + 1/y - 1/(y * (1 + y)**(n - 1))) + 100 / (1 + y)**(n - 1)) / (1 + y)**a if y != 0 else 100 + 100 * i * n
        ai = self.accrint(settlement)
        return round(dirty - ai, 3)
    def ytm(self, settlement: datetime.date, prc: float, *, dcc: str = "act/act") -> float:
        '''
        Yield to maturity with bisection method
        NB: yield is python's reserved keyword, we can not use it as function name (Excel yield())
        **Parameters**
        - settlement: settlement date
        - prc: clean price (market)
        **Return**: float
        **Example**
        from fixedratebond import FRB
        from datetime import date
        # basic info: 25国债22
        maturity = date(2035, 11, 15)
        coupon = 0.0178
        freq = 2
        b = FRB(maturity, coupon, freq)
        d = date.today()
        b.ytm(d, 98.5)
        '''
        ylower, yupper = 0.00, 1.00
        iter, itermax = 0, 500
        tol = 1e-6
        ym = (ylower + yupper) / 2

        while abs(self.price(settlement, ym, dcc = dcc) - prc) > tol:
            if (self.price(settlement, ylower, dcc = dcc) - prc) * (self.price(settlement, ym, dcc = dcc) - prc) < 0:
                yupper = ym
            else:
                ylower = ym
            ym = (ylower + yupper) / 2
            iter += 1
            if iter >= itermax:
                raise Exception("could not find root after " + itermax + " iterations")
        return ym

    def duration(self, settlement: datetime.date, yld: float, *, continuous: bool = False) -> dict[str: float]:
        '''
        Duration: dict of 3 key-value pairs (Macaulay, modified, money)
        **Parameters**
        - settlement: settlement date
        - yld: yield
        - continuous: kwarg, whether to use continuous compounding or not
        **Return**: dict with keys "macaulay", "modified", "money"
        **Example**
        from fixedratebond import FRB
        from datetime import date
        # basic info: 25国债22
        maturity = date(2035, 11, 15)
        coupon = 0.0178
        freq = 2
        b = FRB(maturity, coupon, freq)
        d = date.today()
        b.duration(d, 0.05)
        '''
        bcfs = self.__cfs(settlement)
        y = yld / self.frequency
        n = len(bcfs[2])
        dcfs = [bcfs[2][t] * exp(-bcfs[1][t] * y) for t in range(n)] if continuous else [bcfs[2][t] / (1 + y)**bcfs[1][t] for t in range(n)]
        p = sum(dcfs)
        tdcfs = [bcfs[1][t] * dcfs[t] for t in range(n)]

        macd = sum(tdcfs) / (p * self.frequency)
        modd = macd if continuous else macd / (1 + y)
        mond = modd * p
        return {"macaulay": macd, "modified": modd, "money": mond}

    def convexity(self, settlement: datetime.date, yld: float, *, continuous: bool = False) -> float:
        '''
        Convexity
        **Parameters**
        - settlement: settlement date
        - yld: yield
        - continuous: kwarg, whether to use continuous compounding or not
        **Return**: float
        **Example**
        from fixedratebond import FRB
        from datetime import date
        # basic info: 25国债22
        maturity = date(2035, 11, 15)
        coupon = 0.0178
        freq = 2
        b = FRB(maturity, coupon, freq)
        d = date.today()
        b.convexity(d, 0.05)
        '''
        bcfs = self.__cfs(settlement)
        y = yld / self.frequency
        n = len(bcfs[2])
        dcfs = [bcfs[2][t] * exp(-bcfs[1][t] * y) for t in range(n)] if continuous else [bcfs[2][t] / (1 + y)**bcfs[1][t] for t in range(n)]
        p = sum(dcfs)
        ttdcfs = [(bcfs[1][t])**2 * dcfs[t] for t in range(n)] if continuous else [bcfs[1][t] * (bcfs[1][t] + 1) * dcfs[t] for t in range(n)]
        res = sum(ttdcfs) / (p * (self.frequency)**2) if continuous else sum(ttdcfs) / (p * (1 + y)**2 * (self.frequency)**2)
        return res
