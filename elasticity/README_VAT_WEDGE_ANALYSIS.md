# VAT Effective Wedge Analysis - UK 2022

## Quick Summary
This analysis calculates industry-specific VAT effective wedges using UK Input-Output Tables (2022) to understand why firms bunch below the VAT registration threshold.

**Key Finding**: 90% of industries show negative wedges (would benefit from VAT registration), yet we observe bunching. This suggests compliance costs (~£3-5k/year) are the missing piece.

## The Formula
```
τ_e = λ(1-ρ)τ - τs_c·v
```
Where:
- **τ_e**: Effective VAT wedge (negative = benefits from registration)
- **λ**: B2C share of sales (from IOT data)
- **ρ**: Pass-through rate (UK-calibrated from literature)
- **τ**: VAT rate (20%)
- **s_c**: Input cost share (from A matrix)
- **v**: VAT-eligible input share (estimated)

## Files Overview

### 📊 Data Files
- `iot2022industry.xlsx` - Original UK Input-Output Tables 2022
- `iot_sheet.csv`, `a_sheet.csv` - Converted to CSV for processing

### 🔧 Main Analysis
- `01_main_wedge_calculation.py` - **RUN THIS** - Main calculation script with corrected methodology
- `uk_wedge_calculations_corrected.csv` - Output with all 104 industries

### 📈 Supporting Analysis
- `02_why_negative_wedges.py` - Explains why most wedges are negative
- `03_what_changed_with_correction.py` - Shows what the correction fixed
- `UK_passthrough_evidence.md` - Literature review of UK VAT pass-through rates
- `data_gaps_and_next_steps.md` - What data we still need

## How to Run

```bash
# Run the main analysis
python3 01_main_wedge_calculation.py

# Understand why most wedges are negative
python3 02_why_negative_wedges.py

# See what changed with corrections
python3 03_what_changed_with_correction.py
```

## Key Results

### Industry Distribution
- **90.4%** have negative wedges (benefit from VAT registration)
- **9.6%** have positive wedges (harmed by VAT)

### Examples
| Industry | λ (B2C) | τ_e | Interpretation |
|----------|---------|-----|----------------|
| Retail (G47) | 0.79 | -0.13 | Strong benefit from registration |
| Manufacturing (C101) | 0.34 | -0.12 | Strong benefit |
| Restaurants (I56) | 0.83 | +0.03 | Slightly harmed |
| Personal Services (S96) | 0.84 | +0.09 | Harmed |

### Why Negative Wedges?
Most businesses have negative wedges because:
1. They can reclaim VAT on inputs (worth ~8% of turnover)
2. They pass most VAT burden to customers (especially B2B sales)
3. Input costs are substantial (40-80% of output)

### The Puzzle
If most firms benefit from VAT registration, why do they bunch below the threshold?

**Answer**: The formula misses **compliance costs**:
- Fixed costs: £3-5k/year
- Time burden: 10-20 hours/month
- For a £90k business: 4-6% of turnover

## What Was Corrected?

The main correction was fixing how we calculate λ (B2C share):

**Before**: λ = B2C sales / Column 118 (wrong denominator)
**After**: λ = B2C sales / (Total Intermediate + Total Final Demand)

This didn't change the fundamental result (90% negative wedges) but made the calculations more accurate.

## Next Steps

1. **Add compliance costs** to the formula:
   ```
   τ_e_full = λ(1-ρ)τ - τs_c·v + C/Y
   ```

2. **Validate** against actual UK VAT registration data

3. **Integrate** with bunching estimation model

## Questions for Review

1. Should we use different pass-through rates by industry size?
2. Are the compliance cost estimates (£3-5k) reasonable?
3. Should we model cash flow impacts separately?

## Contact
For questions about this analysis, see the detailed documentation in the supporting files or check the code comments in `vat_wedge_corrected.py`.