# RatesLab | Research Note 01
## Curve-shape risk beyond parallel DV01 neutrality
**Independent research prototype · v0.1 · 24 November 2026**

### Abstract
We construct a simplified single-curve USD OIS valuation framework and compare a single 10-year swap hedge against a four-tenor hedge for a synthetic USD 12 million face-value bond book. Ten deposit and OIS quotes are bootstrapped using log-linear discount factors. The maximum absolute quote repricing error is 7.01e-11 basis points. Across six prescribed curve shocks, the multi-tenor hedge reduces the key-rate DV01 L2 norm from USD 4,821.30 to USD 39.13 per bp, and the worst tested scenario loss from USD 835,220 to USD 4,628. These are deterministic numerical results, not empirical evidence or investment returns. The experiment demonstrates why a zero aggregate DV01 can coexist with substantial curve-shape exposure.

### 1. Research design and data
The synthetic quotes in `data/synthetic_ois.csv` span 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20 and 30 years. Short quotes are simple deposit rates; longer quotes are hypothetical spot-start OIS par rates. All are constructed inputs, not observed prices. The book contains semiannual-coupon bonds: USD 2m at 2Y/3.8%, USD 3m at 5Y/4.2%, USD 5m at 10Y/4.5%, and USD 2m at 20Y/4.7%. The market value is USD 12,352,415.91. The same curve discounts all cash flows, so Treasury/OIS basis, credit and liquidity spread are deliberately excluded. The starting date is abstract time zero, not an actual settlement date. No employer data is used.

Hypotheses: (H1) bootstrap reproduces input instruments; (H2) parallel DV01 neutralization does not eliminate node-level risk; (H3) tenor-diversified hedging lowers zero-node sensitivity and shock losses in this particular book; (H4) dollar convexity improves the parallel-shock approximation relative to DV01 alone. H1 is numerical consistency, not external model validation. H2-H4 are evaluated on the stated deterministic experiment, not statistical hypothesis tests.

### 2. Mathematical framework
Let D(t) denote a positive discount factor, D(0)=1. Deposit: D(T)=1/(1+rT). On each interval, log D(t) is interpolated linearly; the continuous zero rate is z(t)=-log D(t)/t and the simple forward rate is F(a,b)=(D(a)/D(b)-1)/(b-a).

Under the simplified spot-start, single-curve OIS assumptions, the discounted floating leg per unit notional is 1-D(T) and the fixed leg is K times A, where A=sum(alpha_i D(t_i)). The par rate is K*=(1-D(T))/A. Each new pillar is solved by Brent's method in log D, holding earlier nodes fixed. The payer swap PV is N[1-D(T)-KA]; the receiver value is the negative. This telescoping identity assumes aligned accrual/payment endpoints and no already-fixed coupons or lag. Negative rates are allowed; discount factors need not be decreasing. Extrapolation is rejected.

A fixed coupon bond PV equals the sum of discounted coupon and redemption cash flows. YTM is the nominal yield compounded at coupon frequency that reproduces that PV. At a coupon date, accrued interest is zero; off-cycle clean/dirty price and actual day count are not implemented.

For a parallel continuous-zero shock h=0.0001, DV01=[V(z-h)-V(z+h)]/2 in USD/bp. Dollar convexity=[V(z+h)+V(z-h)-2V(z)]/h^2. For shock b in basis points, approximate P&L=-DV01*b+0.5*DollarConvexity*(b*h)^2. Node DV01 bumps one zero-rate knot while retaining log-linear interpolation. Quote PV01 instead bumps each deposit/OIS quote and recalibrates; the two sensitivities are not interchangeable.

For hedge instruments at par, construct matrix A whose columns are node DV01 vectors for USD 1m payer swaps and target r for the bond book. Solve min_w ||r+Aw||_2 by least squares; signed weights map to payer/receiver notionals. The single-tenor alternative sets only aggregate parallel DV01 to zero. No position limits or costs are included. All shocks reprice the original trades and hold contracted coupons and fixed swap rates constant.

### 3. Validation
18 pytest checks passed locally in the original experiment. The suite covers flat-curve discount/forward identities, invalid and duplicate inputs, no extrapolation, negative rates, synthetic quote repricing, zero-coupon analytic PV, bond YTM, par swap NPV, payer/receiver signs, analytic zero-coupon DV01 and convexity, approximate node-risk additivity, parallel hedge, node hedge and quote sensitivity support. Maximum calibration residual: 7.0083e-11 bp. This is internal calibration consistency; an independently implemented QuantLib benchmark has not yet run.

See [calibration results](../outputs/curve.csv). Run the experiment to generate all three figures.

### 4. Results
| Metric | Unhedged | 10Y hedge | Multi-tenor hedge |
|---|---:|---:|---:|
| Parallel DV01 (USD/bp) | 8800.40 | 0.00 | 46.86 |
| Node DV01 L2 (USD/bp) | 4821.30 | 4389.59 | 39.13 |
| Worst loss in six shocks (USD) | 835220 | 83815 | 4628 |

10Y payer swap notional is USD 10.496m. Multi-tenor payer swap notionals are USD 2.020m, 3.040m, 5.020m and 2.014m at 2Y, 5Y, 10Y and 20Y, respectively. The least-squares matrix has full column rank (4). Key-rate risk L2 declines 99.19%; the residual parallel DV01 is USD 46.86/bp because the objective minimizes node risk, not parallel DV01 exactly.

| Scenario (USD P&L) | Unhedged | 10Y hedge | Multi-tenor hedge |
|---|---:|---:|---:|
| Parallel +100 bp | -835220 | 5059 | -4628 |
| Parallel -100 bp | 929110 | 6666 | 4736 |
| Bear steepener | -586469 | 43576 | -1673 |
| Bear flattener | -325040 | -55545 | -3334 |
| Belly +75 bp | -139706 | -83815 | -1804 |
| Twist | -249588 | 92484 | 1283 |

The single 10Y hedge eliminates local parallel DV01 but leaves substantial tenor mismatch. At +100 bp, first-order P&L error is USD 44,820 on the unhedged book; incorporating dollar convexity reduces it to USD 2,041. At +200 bp these errors are USD 171,722 and USD 15,720 respectively, showing higher-order effects become material. These are absolute approximation errors, not hedge P&L.

### 5. Limitations and next research
The synthetic bond and swap maturities are deliberately aligned, making the multi-tenor hedge favorable. A less aligned portfolio, different coupon schedules, separate curves, transaction costs and constraints can produce much weaker results. Six prescribed shocks do not constitute historical backtesting, VaR or statistical validation. The OIS simplified model omits dates, ACT/360, calendars, payment lag, fixing history, futures convexity adjustment, CSA and collateral variation. The curve is bootstrapped in a broad fixed numerical bracket and rejects extrapolation; the model does not establish global no-arbitrage beyond positive discount factors and internal quote consistency. An independent date-based QuantLib comparison and alternative interpolation are the next gates. No employer or university endorsement is represented.

### References and further reading
- Federal Reserve Bank of New York, [SOFR reference rate](https://www.newyorkfed.org/markets/reference-rates/sofr). Overnight fixing, not an OIS term curve.
- FRED, [DGS10 constant maturity Treasury yield](https://fred.stlouisfed.org/series/DGS10). Treasury yield, not an OIS quote.
- QuantLib Guide, [Curve bootstrapping](https://www.quantlibguide.com/Curve%20bootstrapping.html), [Different kinds of swaps](https://www.quantlibguide.com/Different%20kinds%20of%20swaps.html). Implementation references for the next independent benchmark.
- Nelson, C. R., and Siegel, A. F. (1987). Parsimonious Modeling of Yield Curves. Journal of Business, 60(4), 473–489. Planned comparison, not yet implemented.
