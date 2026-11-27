# RatesLab

**Fixed Income Quantitative Research & Pricing Engine** | v0.1.0

**[Open interactive research workbench](https://rateslab-workbench.vercel.app)** — browser-based controls, charts and calculations; no local installation required.
### Market-data provenance

Bond Explorer includes a verified official Treasury observation dated 2026-11-25, and 2026-11-24 for comparison, from [U.S. Treasury Daily Treasury Par Yield Curve Rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?field_tdr_date_value_month=202611&type=daily_treasury_yield_curve). Refresh attempts the Treasury monthly CSV endpoint directly; if browser access fails, the dated official observation remains visible and official CSV import is available. No automatic synthetic fallback, API key, or paid data backend. Imported CSV provenance is not independently authenticated. Treasury constant-maturity par yields are benchmark rates, not individual security prices, zero rates or OIS swap quotes. The OIS research lab continues to use explicitly synthetic inputs.

### Interactive modes

- **Bond Explorer (default):** instant, browser-native fixed-coupon bond pricing. Default inputs use the selected maturity's published U.S. Treasury par yield as both coupon and yield for a hypothetical par bond. Custom coupon and yield are optional. Explore exact price changes under yield shocks, annual coupon income, Macaulay/modified duration, finite-difference DV01 and contractual cash flows. Assumes pricing on a coupon date, no call or default, and no accrued interest. This is a flat-yield educational calculator, not a yield-curve calibration.
- **Portfolio Lab:** the existing Python deposit/OIS curve, exact portfolio repricing, zero-node risk and swap hedging engine, with guided scenario explanations, true maturity spacing, signed P&L bars, and before/after hedge comparisons. Illustrative quotes are explicitly identified; no Treasury yields are substituted for OIS quotes. First custom run loads Pyodide; initial results are the checked-in synthetic example.

The interface uses blue for valuation, green/red for signed price changes, and amber for rate sensitivity. Both modes run in the browser, require no API key or paid service, and do not model transaction costs, margin, liquidity, tax or credit losses.



Independent research project — prototype, not a production valuation or trading system.

RatesLab investigates whether parallel-DV01 neutrality is sufficient to hedge curve-shape risk. It builds a simplified USD discount curve from synthetic deposit and OIS par quotes, prices a fixed-income book, measures both zero-node and market-quote sensitivities, and compares single-tenor and multi-tenor swap hedges under six deterministic shocks.

## Reproduce

Python 3.10 or newer. No API keys or paid feeds are required.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[test]'
python -m pytest -q
python -m rateslab.experiment
```

The last command writes CSV, JSON and PNG outputs under `outputs/`. The experiment is deterministic, without randomized inputs. GitHub Actions is configured to run tests and save regenerated outputs as artifacts.

## Results: synthetic experiment, not historical performance

| Metric | Unhedged | 10Y hedge | Multi-tenor hedge |
|---|---:|---:|---:|
| Parallel DV01 (USD/bp) | 8,800.40 | 0.00 | 46.86 |
| Key-rate DV01 L2 (USD/bp) | 4,821.30 | 4,389.59 | 39.13 |
| Worst loss among six shocks (USD) | 835,220 | 83,815 | 4,628 |

Ten input quotes reprice to a maximum absolute error of 7.01e-11 bp. The multi-tenor hedge reduces key-rate risk norm by 99.19% in this particular synthetic book. The comparison does not imply future performance, executable pricing, or general hedge effectiveness.

See [stress P&L](outputs/stress.csv) and [curve calibration](outputs/curve.csv).

## Structure

```text
rateslab/core.py          # curve, instruments, risk and hedging
rateslab/experiment.py    # deterministic experiment and figures
data/synthetic_ois.csv    # artificial inputs (rates in decimal)
tests/test_core.py        # 18 unit and numerical validation tests
outputs/                 # machine-readable results; plots generated on run
reports/research.md       # research methods, results and limitations
pyproject.toml            # package and dependencies
```

## Conventions and limitations

Spot-start, single-curve OIS, annual fixed leg, simplified year fractions, no holiday calendar, accrued interest, settlement/payment lags, daily fixings, CSA differences, credit/funding spreads, transaction costs or margin. The bond value is an illustrative present value at a coupon date, not an executable Treasury quote. Zero-node risk and rebootstrap quote risk are intentionally separate. The hedge is unconstrained least squares on zero-node DV01, not a tradable portfolio recommendation. All inputs are synthetic; no external model validation has been performed.

Public data plan: NY Fed SOFR fixings and FRED Treasury constant-maturity series for context; a documented source of OIS par instruments is required for empirical OIS calibration. SOFR fixings and Treasury par yields are not substitutes for an OIS term structure. QuantLib date/convention benchmark, alternative interpolation, historical tests, Nelson-Siegel-Svensson and Hull-White calibration remain open research tasks.

See [research report](reports/research.md).
