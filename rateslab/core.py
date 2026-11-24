"""USD fixed-income research engine. Rates are decimals, times are year fractions.
Simplified spot-start single-curve OIS: no calendars, lags, fixings or collateral basis.
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import brentq

BP = 1e-4

@dataclass(frozen=True)
class Curve:
    times: np.ndarray
    discounts: np.ndarray

    def __post_init__(self):
        t = np.asarray(self.times, dtype=float).copy()
        d = np.asarray(self.discounts, dtype=float).copy()
        if t.ndim != 1 or t.shape != d.shape or len(t) < 2 or not np.all(np.isfinite(t)) or not np.all(np.isfinite(d)):
            raise ValueError('Invalid curve arrays')
        if t[0] != 0 or d[0] != 1 or np.any(np.diff(t) <= 0) or np.any(d <= 0):
            raise ValueError('Require increasing times, D(0)=1, positive discount factors')
        t.setflags(write=False); d.setflags(write=False)
        object.__setattr__(self, 'times', t); object.__setattr__(self, 'discounts', d)

    def df(self, t):
        t = np.asarray(t, dtype=float)
        if np.any(~np.isfinite(t)) or np.any(t < 0) or np.any(t > self.times[-1] + 1e-10):
            raise ValueError('Time outside calibrated curve')
        return np.exp(np.interp(t, self.times, np.log(self.discounts)))

    def zero(self, t):
        t = np.asarray(t, dtype=float)
        if np.any(t <= 0): raise ValueError('Zero rate requires t > 0')
        return -np.log(self.df(t)) / t

    def forward(self, start, end):
        if not 0 <= start < end: raise ValueError('Invalid forward interval')
        return (self.df(start)/self.df(end)-1)/(end-start)

    def shift(self, bps):
        """Zero-rate node shocks, not market quote shocks."""
        s = np.broadcast_to(np.asarray(bps, dtype=float), self.times.shape)
        return Curve(self.times, self.discounts * np.exp(-self.times*s*BP))

@dataclass(frozen=True)
class Quote:
    kind: str
    maturity: float
    rate: float


def schedule(maturity, frequency=1):
    if not np.isfinite(maturity) or maturity <= 0 or frequency not in (1,2,4,12):
        raise ValueError('Invalid maturity or frequency')
    times = np.arange(1, int(np.floor(maturity*frequency+1e-10))+1)/frequency
    if len(times) == 0 or times[-1] < maturity-1e-10:
        times = np.append(times, maturity)
    return times, np.diff(np.r_[0., times])


def par_swap(curve, maturity):
    t, accrual = schedule(maturity)
    return (1-curve.df(maturity))/np.dot(accrual, curve.df(t))


def implied_quote(curve, quote):
    if quote.kind == 'deposit': return (1/curve.df(quote.maturity)-1)/quote.maturity
    if quote.kind == 'ois': return par_swap(curve, quote.maturity)
    raise ValueError('Unknown quote kind')


def bootstrap(quotes):
    """Solve each pillar, interpolating log D between solved and trial knots."""
    quotes = sorted(quotes, key=lambda q:q.maturity)
    if not quotes: raise ValueError('No quotes')
    times, dfs = [0.], [1.]
    for q in quotes:
        if not np.isfinite(q.maturity) or not np.isfinite(q.rate) or q.maturity <= times[-1]:
            raise ValueError('Invalid or duplicate quote')
        if q.kind == 'deposit':
            if 1+q.rate*q.maturity <= 0: raise ValueError('Invalid deposit')
            df = 1/(1+q.rate*q.maturity)
        elif q.kind == 'ois':
            def residual(logdf):
                trial=Curve(np.r_[times,q.maturity],np.r_[dfs,np.exp(logdf)])
                return implied_quote(trial,q)-q.rate
            df=np.exp(brentq(residual,-50.,20.,xtol=1e-13))
        else: raise ValueError('Unknown quote kind')
        times.append(q.maturity); dfs.append(df)
    return Curve(np.array(times),np.array(dfs))

@dataclass(frozen=True)
class Bond:
    notional: float
    maturity: float
    coupon: float
    frequency: int = 2

    def pv(self, curve):
        t,a=schedule(self.maturity,self.frequency)
        cf=self.notional*self.coupon*a
        cf[-1]+=self.notional
        return float(cf @ curve.df(t))

    def ytm(self, price):
        t,a=schedule(self.maturity,self.frequency)
        cf=self.notional*self.coupon*a; cf[-1]+=self.notional
        if price <= 0 or self.notional <= 0 or self.coupon < 0: raise ValueError('YTM requires positive price and nonnegative cashflows')
        # Nominal yield compounded at coupon frequency, including fractional last period.
        return brentq(lambda y: cf @ (1+y/self.frequency)**(-self.frequency*t)-price,-self.frequency+1e-8,100)

@dataclass(frozen=True)
class Swap:
    notional: float
    maturity: float
    fixed_rate: float
    payer: bool = True

    def pv(self,curve):
        t,a=schedule(self.maturity)
        floating=1-curve.df(self.maturity)
        fixed=self.fixed_rate*(a@curve.df(t))
        return float(self.notional*(floating-fixed)*(1 if self.payer else -1))


def pv(positions,curve):
    return sum(p.pv(curve) for p in positions)


def parallel_risk(positions,curve):
    """Positive DV01 means value falls with higher zero rates; convexity in USD/rate^2."""
    base=pv(positions,curve); down=pv(positions,curve.shift(-1)); up=pv(positions,curve.shift(1))
    return (down-up)/2, (up+down-2*base)/BP**2


def key_rate_risk(positions,curve):
    risk=[]
    for i in range(1,len(curve.times)):
        s=np.zeros(len(curve.times)); s[i]=1
        risk.append((pv(positions,curve.shift(-s))-pv(positions,curve.shift(s)))/2)
    return np.array(risk)


def quote_risk(positions,quotes):
    """Market quote PV01: independently bump each input and rebootstrap."""
    quotes=sorted(quotes,key=lambda q:q.maturity)
    results=[]
    for i,q in enumerate(quotes):
        up=quotes.copy(); down=quotes.copy()
        up[i]=Quote(q.kind,q.maturity,q.rate+BP); down[i]=Quote(q.kind,q.maturity,q.rate-BP)
        results.append((pv(positions,bootstrap(down))-pv(positions,bootstrap(up)))/2)
    return np.array(results)


def hedge(positions,curve,maturities,mode='key'):
    """Unconstrained least-squares swap hedge; signed USD notionals, payer positive."""
    unit=1e6
    swaps=[Swap(unit,t,par_swap(curve,t)) for t in maturities]
    if mode=='key':
        target=key_rate_risk(positions,curve)
        a=np.column_stack([key_rate_risk([s],curve) for s in swaps])
    elif mode=='parallel':
        target=np.array([parallel_risk(positions,curve)[0]])
        a=np.array([[parallel_risk([s],curve)[0] for s in swaps]])
    else: raise ValueError('Unknown hedge mode')
    w,_,rank,_=np.linalg.lstsq(a,-target,rcond=None)
    hedges=[Swap(float(abs(x)*unit),s.maturity,s.fixed_rate,bool(x>=0)) for x,s in zip(w,swaps)]
    return hedges,w*unit,rank
