# Dynamic Modeling — threshold variants & unified model

These files extend the firm-VAT FOC dynamic-modeling work (see PR #17 for the core
`reverse_productivity_estimation.py` / `vat_optimization_model.html`).

## Unified model
- **`vat_model_unified.py`** — implements all 8 sections of `vat_optimization_model.html`
  in one script: Cobb-Douglas marginal cost, sigmoid tax + FOC, FOC+uncertainty,
  polynomial no-VAT counterfactual, and elasticity extraction (production / bunching /
  local / revealed). Reads `synthetic_firms_with_productivity.csv`. Outputs:
  - `vat_model_unified_results.png`, `vat_model_unified_summary.txt`
    (per-firm CSV is gitignored — large).

## Two threshold assumptions (£85k vs £90k)
The synthetic data can be generated under either VAT-threshold assumption:

- **`gen_full_param.py`** — parameterized copy of `generate_synthetic_data.py`, driven by
  the `VAT_THRESHOLD` env var (sets the band boundary in `_map_to_hmrc_bands` plus the
  VAT-registration flags). Run from `analysis/` so `project_root` resolves to `../data`:
  ```bash
  VAT_THRESHOLD=85 python gen_full_param.py   # -> synthetic_firms_85k.csv (step at £85k)
  VAT_THRESHOLD=90 python gen_full_param.py   # -> synthetic_firms_90k.csv (step at £90k)
  ```
  (Output CSVs are gitignored — ~220MB each. The £85k data reproduces the original
  2023-24 dataset; £90k is the current-law variant.)

- **`plot_turnover_two_versions.py`** — turnover distributions for both datasets:
  `turnover_distribution_85k.png`, `turnover_distribution_90k.png`,
  `turnover_distribution_compare.png` (overlay showing the step at 85k vs 90k).

- **`bunching_analysis_85k.py`** / **`bunching_analysis_90k.py`** — the bunching pipeline
  run on each dataset (threshold £85k→new £95k, and £90k→new £100k):
  `bunching_analysis_85k.png`, `bunching_analysis_90k.png`.

## Notes
- The £85k threshold uses 2023-24 data (the VAT threshold was £85k then); £90k is current.
- Large synthetic CSVs are gitignored — regenerate with the commands above.
