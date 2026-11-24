# Research and engineering roadmap

## Role alignment (public job descriptions, not proprietary standards)
- JPMorgan Quantitative Finance: https://www.jpmorganchase.com/careers/explore-opportunities/programs/quant-fin-programs — pricing mathematics, research and numerical methods.
- Morgan Stanley Interest Rate Strat: https://ms.wd5.myworkdayjobs.com/External/job/New-York-New-York-United-States-of-America/Interest-Rate-Strat---Fixed-Income---Associate---Vice-President_JR036262 — curve modelling, P&L, sensitivities and stress tests.
- Goldman Sachs Quantitative Rates Trading Strat: https://higher.gs.com/roles/180880 — rates pricing and hedging optimization.
- BlackRock Analytics and Modeling: https://careers.blackrock.com/students-and-graduates-functions-analytics-modeling — valuation, model risk, quantitative engineering.

## Milestones and acceptance criteria
| Release | Scope | Gate |
|---|---|---|
| v0.1 (implemented) | synthetic OIS curve, pricing, finite differences, hedge | 18 unit checks pass; max quote error < 1e-6 bp; six reproducible shocks |
| v0.2 | date-based QuantLib OIS benchmark, ACT/360, calendars, settlement, payment lag, fixings, explicit quote metadata | same conventions and inputs; define tolerance before comparison; report residual discrepancies; no fabricated data |
| v0.3 | real dated OIS quotes (if lawful free source available), Treasury NSS curve as separate model, log-linear vs alternative interpolation | dated provenance, no stale data substitution, held-out maturity error and stability diagnostics |
| v0.4 | historical rolling hedge and P&L explain, quote-PV01 hedge, transaction costs, tenor mismatch, constraints | time-ordered evaluation, benchmark and sensitivity to costs; disclose unavailable data |
| v0.5 | Hull-White short-rate model and swaption calibration (only if suitable data) | analytic bond benchmark, calibration residuals, numerical convergence, out-of-sample validation |
| v1.0 | final report, CI, packaging, reproducible figures, presentation | independent review, code walkthrough by candidate, transparent scope and affiliations |

## Interview mastery checklist
Explain discount-factor bootstrap, forward rates, fixed and floating legs, par swap vs off-market swap, payer/receiver signs, DV01 vs market quote PV01, convexity, key-rate hedging, model assumptions and least squares. Derive the formulas without reading AI-generated code; independently reproduce the experiment and implement at least one extension. Only claim work personally completed and understood. Use university attribution only within the scope of actual approval; do not imply faculty supervision or an official research position without authorization.
