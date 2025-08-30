
# VAT Effective Wedge — Agent TODO (Concise)

**Current Confidence (self-reported): MODERATE (65–70%)**  
- High: τ=20% (UK), s_c from IO tables (simplified), λ for obvious sectors (retail/hospitality high, manufacturing low).  
- Low: ρ pass‑through (heuristics), v VAT‑eligible inputs (guesses), λ for mixed sectors (professional/ICT).

---

## Critical Uncertainties to Resolve
1) **IOT Interpretation**: Avoid s_c > 1 artifacts. Confirm whether you're using *industry-by-industry requirements* vs *use* at basic/purchasers' prices and netting imports properly.  
2) **ρ (Pass-through)**: Replace heuristics with sector-specific estimates from natural experiments / UK evidence where available.  
3) **v (VAT-eligible input share)**: Replace guesses with reclaimability mapping from HMRC notices applied to IO cost bundles.  
4) **Integration Test**: Fix the bunching integration script and validate signs/magnitudes against known UK bunching patterns around the VAT threshold.

---

## Minimal Data Ingests (UK-first)
- **ONS Supply–Use / Input–Output (latest year)**: Use & Requirements matrices (products × industries).  
- **ONS Annual Business Survey (ABS)**: Purchases vs turnover by SIC for s_c cross-checks.  
- **HMRC VAT guidance**: VAT Notice 700, 706 (Partial Exemption), 700/64 (Motoring), VAT Act 1994 Sch. 9 (exemptions).  
- **Literature table for ρ**: Kosonen 2015; Benzarti & Carloni 2019; Benedek et al.; Carbonnier 2007. Record sector, reform type, horizon, and pass-through.

---

## Step-by-Step Tasks (make each cell runnable)
**T1. Compute λ (B2C share) from Use table**  
- For each CPA product → sector mapping, compute:  
  `lambda = (HFCE + NPISH) / (Total Use − Imports)` at purchasers’ prices.  
- Adjust retail trade margins: allocate underlying goods’ HFCE to retail sector where appropriate.  
- Export **sector_lambda.csv** with columns: sector, lambda, notes.

**T2. Compute s_c (intermediate input share)**  
- From the **industry-by-industry requirements** matrix: `s_c = sum_j a_{j,i}` (column sum of intermediate coefficients).  
- Cross-check with ABS purchases/turnover; flag sectors where |Δ| > 10 p.p.  
- Export **sector_s_c.csv**.

**T3. Estimate v (VAT-eligible input share)**  
- Build a **reclaimability matrix**: wages=0, finance/insurance=0, rent/land=0 (unless opted to tax), business entertainment=0, blocked cars=0; materials/utilities/most services=1.  
- Join with each sector’s IO intermediate cost bundle (by product) to compute `v = (Σ eligible_cost) / (Σ total_intermediate_cost)`.  
- Export **sector_v.csv** + a log of blocked categories by sector.

**T4. Assemble ρ (pass-through) priors**  
- Create **rho_lit.csv** with columns: sector, study, country, reform type (std/reduced/reclass), short-run/long-run horizon, point estimate, CI.  
- Default rules until UK evidence is found:  
  - Retail goods std-rate changes: ρ≈0.8–1.0  
  - Personal services reduced-rate cuts: ρ≈0.3–0.6  
  - Restaurants (FR 2009 cut): ρ≈0.1–0.3  
  - Hairdressing (FI cut): ρ≈0.4–0.6  

**T5. Compute τ_e**  
- Merge lambda/s_c/v with ρ priors; compute `tau_e = lambda*(1−rho)*tau − tau*s_c*v` at τ=0.20.  
- Output **tau_e_by_sector.csv** and a plot of τ_e with error bars from parameter ranges.

**T6. Validation hooks**  
- Check sign expectations: retail/manufacturing τ_e < 0; personal services/hospitality τ_e > 0.  
- If not, print which parameter drives the contradiction using the partials:  
  `dτ_e/dλ = (1−ρ)τ`, `dτ_e/dρ = −λτ`, `dτ_e/ds_c = −τv`, `dτ_e/dv = −τs_c`.

---

## File I/O Contracts
- Inputs: `use_table.csv`, `requirements_matrix.csv`, `abs_purchases_turnover.csv`, `sector_map.csv` (CPA→sector), `hmrc_reclaim_rules.yaml`, `rho_lit_raw.csv`  
- Outputs: `sector_lambda.csv`, `sector_s_c.csv`, `sector_v.csv`, `rho_lit.csv`, `tau_e_by_sector.csv`, `tau_e_plot.png`, `validation_report.md`

---

## Red Flags & Fixes
- **s_c > 1**: You summed flows at purchasers’ prices or mixed total output with total use. Switch to coefficients (requirements) or divide by total output at **basic prices**.  
- **v too high in services**: You likely treated wages/rent as reclaimable; they are not.  
- **ρ > 1 or < 0**: Cap to [0,1] unless the study explicitly estimates overshifting; document those cases separately.

---

## Minimal Pseudocode (drop into notebook cells)

```python
# T1 λ
use = pd.read_csv("use_table.csv")
fd_cols = ["HFCE","NPISH"]
use["final_household"] = use[fd_cols].sum(axis=1)
use["total_use_netM"] = use["total_use"] - use["imports"]
lambda_df = (use.groupby("sector", as_index=False)
               .apply(lambda g: pd.Series({"lambda": g["final_household"].sum()/g["total_use_netM"].sum()})))
lambda_df.to_csv("sector_lambda.csv", index=False)

# T2 s_c
A = pd.read_csv("requirements_matrix.csv")  # a_{j,i} coefficients
s_c = (A.drop(columns=["industry"])
         .set_index(A["industry"]).sum(axis=0).rename("s_c").reset_index())
s_c.to_csv("sector_s_c.csv", index=False)

# T3 v
bundle = pd.read_csv("intermediate_bundle.csv")  # sector, product, cost
rules = yaml.safe_load(open("hmrc_reclaim_rules.yaml"))
elig = pd.DataFrame(rules["eligibility"])       # product/category, reclaimable 0/1
v = (bundle.merge(elig, on="product")
          .assign(eligible_cost=lambda d: d["cost"]*d["reclaimable"])
          .groupby("sector").apply(lambda g: g["eligible_cost"].sum()/g["cost"].sum())
          .rename("v").reset_index())
v.to_csv("sector_v.csv", index=False)

# T4 ρ
rho = (pd.read_csv("rho_lit_raw.csv")
         .groupby("sector")["rho_point"].median().rename("rho").reset_index())
rho.to_csv("rho_lit.csv", index=False)

# T5 τ_e
params = (lambda_df.merge(s_c, on="sector")
                    .merge(v, on="sector")
                    .merge(rho, on="sector"))
tau = 0.20
params["tau_e"] = params["lambda"]*(1-params["rho"])*tau - tau*params["s_c"]*params["v"]
params.to_csv("tau_e_by_sector.csv", index=False)
```

---

## Acceptance Criteria
- `tau_e_by_sector.csv` produced with no NaNs; `validation_report.md` states pass/fail for sign checks.  
- All intermediate CSVs included; script documents any sector with missing IO mappings or reclaim rules.
