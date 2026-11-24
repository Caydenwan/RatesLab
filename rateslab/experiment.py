"""Reproduce all v0.1 experiment outputs: python -m rateslab.experiment."""
import csv, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .core import *

ROOT=Path(__file__).resolve().parents[1]

def run(root=ROOT):
    out=root/'outputs'; out.mkdir(exist_ok=True)
    with (root/'data/synthetic_ois.csv').open() as f:
        qs=[Quote(r['kind'],float(r['maturity']),float(r['rate'])) for r in csv.DictReader(f)]
    c=bootstrap(qs)
    bonds=[Bond(2e6,2,.038),Bond(3e6,5,.042),Bond(5e6,10,.045),Bond(2e6,20,.047)]
    h1,w1,r1=hedge(bonds,c,[10],'parallel')
    h2,w2,r2=hedge(bonds,c,[2,5,10,20],'key')
    books={'Unhedged':bonds,'10Y DV01 hedge':bonds+h1,'Multi-tenor key-rate hedge':bonds+h2}
    times=c.times
    scenarios={'Parallel +100bp':np.full(len(times),100.),'Parallel -100bp':np.full(len(times),-100.),
               'Bear steepener':np.interp(times,[0,2,10,30],[0,10,80,120]),
               'Bear flattener':np.interp(times,[0,2,10,30],[100,100,25,0]),
               'Belly +75bp':np.interp(times,[0,2,5,10,30],[0,0,75,0,0]),
               'Twist':np.interp(times,[0,2,10,30],[-75,-75,50,100])}
    summary={}
    for name,ps in books.items():
        d,cv=parallel_risk(ps,c); kr=key_rate_risk(ps,c)
        summary[name]={'pv':pv(ps,c),'dv01':d,'dollar_convexity':cv,'key_rate_l2':float(np.linalg.norm(kr)),
                       'key_rate_dv01':kr.tolist(), 'quote_pv01':quote_risk(ps,qs).tolist(), 'scenario_pnl':{s:pv(ps,c.shift(sh))-pv(ps,c) for s,sh in scenarios.items()}}
    errors=[(implied_quote(c,q)-q.rate)*1e4 for q in qs]
    with (out/'curve.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['maturity_years','kind','input_rate_decimal','discount_factor','zero_rate_decimal','repricing_error_bp'])
        for q,e in zip(qs,errors): w.writerow([q.maturity,q.kind,q.rate,float(c.df(q.maturity)),float(c.zero(q.maturity)),e])
    with (out/'stress.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['scenario',*books]);
        for s in scenarios: w.writerow([s,*[summary[n]['scenario_pnl'][s] for n in books]])
    # deterministic local sensitivity approximation vs exact repricing
    d,cv=parallel_risk(bonds,c); base=pv(bonds,c)
    approx=[]
    for bps in [-200,-100,-50,-10,10,50,100,200]:
        exact=pv(bonds,c.shift(bps))-base; linear=-d*bps; second=linear+.5*cv*(bps*BP)**2
        approx.append({'shock_bp':bps,'exact':exact,'linear':linear,'quadratic':second,'linear_abs_error':abs(exact-linear),'quadratic_abs_error':abs(exact-second)})
    result={'data':'Synthetic, not market quotes','max_repricing_error_bp':max(abs(x) for x in errors),'hedge_notionals':{'10Y':w1.tolist(),'2Y_5Y_10Y_20Y':w2.tolist()},'hedge_rank':[int(r1),int(r2)],'books':summary,'approximation':approx}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':160})
    grid=np.linspace(.25,30,300)
    fig,ax=plt.subplots(figsize=(8,4)); ax.plot(grid,c.zero(grid)*100,label='Continuous zero rate'); ax.scatter([q.maturity for q in qs],[q.rate*100 for q in qs],label='Synthetic deposit/OIS quotes',s=24); ax.set(xlabel='Maturity (years)',ylabel='Rate (%)',title='Calibrated USD discount curve'); ax.legend(frameon=False); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(out/'curve.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.7)); x=np.arange(len(scenarios)); width=.25
    for i,n in enumerate(books): ax.bar(x+(i-1)*width,[summary[n]['scenario_pnl'][s]/1000 for s in scenarios],width,label=n)
    ax.set_xticks(x,list(scenarios),rotation=18,ha='right'); ax.set(ylabel='Exact P&L (USD thousands)',title='Scenario P&L: unhedged vs two hedge designs'); ax.axhline(0,color='gray',lw=.8); ax.legend(frameon=False); ax.grid(axis='y',alpha=.2); fig.tight_layout(); fig.savefig(out/'stress.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.5)); x=np.arange(len(qs));
    for i,n in enumerate(books): ax.bar(x+(i-1)*width,summary[n]['key_rate_dv01'],width,label=n)
    ax.set_xticks(x,[str(q.maturity) for q in qs]); ax.set(xlabel='Zero-rate node (years)',ylabel='DV01 (USD / bp)',title='Key-rate risk before and after hedging'); ax.axhline(0,color='gray',lw=.8); ax.legend(frameon=False); ax.grid(axis='y',alpha=.2); fig.tight_layout(); fig.savefig(out/'key_rates.png'); plt.close(fig)
    return result

if __name__=='__main__':
    r=run(); print(json.dumps(r,indent=2))
