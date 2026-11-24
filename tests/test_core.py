import numpy as np
import pytest
from rateslab.core import *

@pytest.fixture
def flat():
    return Curve(np.array([0,1,2,5,10]),np.exp(-.04*np.array([0,1,2,5,10])))

@pytest.fixture
def qs():
    return [Quote('deposit',.5,.043),Quote('ois',1,.04),Quote('ois',2,.039),Quote('ois',5,.041),Quote('ois',10,.043)]

def test_flat_discount(flat): assert flat.df(3)==pytest.approx(np.exp(-.12))
def test_flat_forward(flat): assert flat.forward(1,2)==pytest.approx(np.exp(.04)-1)
def test_no_extrapolation(flat):
    with pytest.raises(ValueError): flat.df(11)
def test_invalid_curve():
    with pytest.raises(ValueError): Curve([0,1],[1,0])
def test_duplicate_quotes(qs):
    with pytest.raises(ValueError): bootstrap(qs+[qs[0]])
def test_repricing(qs):
    c=bootstrap(qs)
    assert max(abs(implied_quote(c,q)-q.rate) for q in qs)<1e-10

def test_deposit(qs): assert bootstrap(qs).df(.5)==pytest.approx(1/(1+.043*.5))
def test_negative_rate():
    c=bootstrap([Quote('deposit',.5,-.01),Quote('ois',1,-.008)])
    assert c.df(.5)>1 and par_swap(c,1)==pytest.approx(-.008)
def test_zero_coupon(flat): assert Bond(1e6,5,0).pv(flat)==pytest.approx(1e6*np.exp(-.2))
def test_bond_ytm(flat):
    b=Bond(1e6,5,.05); assert b.ytm(b.pv(flat))==pytest.approx(2*(np.exp(.04/2)-1))
def test_par_swap(flat): assert Swap(1e6,5,par_swap(flat,5)).pv(flat)==pytest.approx(0,abs=1e-8)
def test_swap_sign(flat): assert Swap(1e6,5,.035).pv(flat)==-Swap(1e6,5,.035,False).pv(flat)
def test_payer_rising_rates(flat):
    s=Swap(1e6,5,par_swap(flat,5)); assert s.pv(flat.shift(100))>0

def test_analytic_dv01(flat):
    b=Bond(1e6,5,0); d,c=parallel_risk([b],flat)
    assert d==pytest.approx(5*b.pv(flat)*BP,rel=1e-6)
    assert c==pytest.approx(25*b.pv(flat),rel=1e-6)
def test_key_sum(flat):
    ps=[Bond(1e6,5,.04)]; assert sum(key_rate_risk(ps,flat))==pytest.approx(parallel_risk(ps,flat)[0],rel=1e-6)
def test_parallel_hedge(flat):
    ps=[Bond(1e6,5,.04)]; h,_,_=hedge(ps,flat,[5],'parallel')
    assert parallel_risk(ps+h,flat)[0]==pytest.approx(0,abs=1e-8)
def test_key_hedge(flat):
    ps=[Bond(1e6,5,.04),Bond(2e6,10,.035)]; h,_,_=hedge(ps,flat,[2,5,10])
    assert np.linalg.norm(key_rate_risk(ps+h,flat))<np.linalg.norm(key_rate_risk(ps,flat))
def test_quote_risk(qs):
    r=quote_risk([Bond(1e6,5,.04)],qs); assert len(r)==len(qs) and abs(r[-1])<1e-8
