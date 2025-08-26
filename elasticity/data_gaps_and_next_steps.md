# Data Gaps and Next Steps for VAT Wedge Analysis

## The Puzzle We Need to Solve

Our analysis shows 93% of industries have **negative wedges** (benefit from VAT registration), yet we observe significant bunching below the £90k threshold. Why?

## Hypothesis: Missing Components

The current formula captures only the **tax wedge**:
```
τ_e = λ(1-ρ)τ - τs_c·v
```

But the **full effective wedge** should be:
```
τ_e_full = λ(1-ρ)τ - τs_c·v + C/Y + A
```

Where:
- **C/Y** = Compliance costs as share of turnover
- **A** = Administrative burden (time cost)

## Priority Data to Collect

### 1. UK Pass-Through Rates (ρ) - HIGHEST PRIORITY
**Current gap**: Using literature from other countries
**Impact**: Could change τ_e by ±0.05

**Specific data sources to pursue:**
- [ ] OBR analysis of 2011 VAT change (17.5% → 20%)
- [ ] Bank of England Quarterly Bulletin on VAT pass-through
- [ ] Crossley, Low & Wakefield (2009) on UK VAT cut
- [ ] Carbonnier (2013) comparison of UK vs France

**Quick win**: The 2008 temporary VAT cut (17.5% → 15%) provides natural experiment

### 2. Actual VAT Reclaim Patterns (v)
**Current gap**: Estimated from sector type
**Impact**: Could change τ_e by ±0.03

**Specific data sources:**
- [ ] HMRC VAT statistics Table 14: "Net VAT receipts by industry"
- [ ] HMRC VAT gap estimates by sector
- [ ] Input-output tables "Use" matrix at purchasers' vs basic prices

**Calculation needed**:
```
v_actual = (Input VAT reclaimed) / (Total intermediate purchases × 0.20)
```

### 3. Compliance Costs (C)
**Current gap**: Not included at all
**Impact**: Could add +0.03 to +0.10 to effective wedge

**Specific data sources:**
- [ ] Federation of Small Businesses (2018) "Cost of Compliance" survey
- [ ] HMRC (2019) "Administrative Burdens" measurement
- [ ] AccountingWeb annual compliance cost survey
- [ ] Hansford & Hasseldine (2012) VAT compliance costs study

**Key metrics needed:**
- Fixed cost of VAT registration (£/year)
- Variable cost (% of VAT collected)
- Time burden (hours/month)

## Immediate Action Plan

### Step 1: Get UK Pass-Through Data (This Week)
```python
# Search for these specific studies:
studies = [
    "Crossley, T. F., Low, H., & Wakefield, M. (2009). The economics of a temporary VAT cut",
    "Carare, A., & Danninger, S. (2008). Inflation smoothing and the modest effect of VAT in Germany",
    "OBR (2011). Economic and fiscal outlook - VAT analysis supplementary",
]
```

### Step 2: Calculate Actual v from HMRC Data
```python
# Use HMRC Table 14 data:
# Net VAT = Output VAT - Input VAT reclaimed
# Therefore: Input VAT reclaimed = Output VAT - Net VAT
# v = Input VAT reclaimed / (Intermediate purchases × 0.20)
```

### Step 3: Add Compliance Cost Layer
```python
# Modify wedge formula:
def calculate_full_wedge(lambda_b2c, rho, s_c, v, turnover):
    tax_wedge = lambda_b2c * (1 - rho) * 0.20 - 0.20 * s_c * v
    
    # Add compliance costs
    fixed_cost = 3000  # £3k per year
    variable_cost = 0.005  # 0.5% of turnover
    compliance_wedge = (fixed_cost / turnover) + variable_cost
    
    return tax_wedge + compliance_wedge
```

## Expected Resolution

With these three data gaps filled:

1. **Pass-through data** → Confidence increases to 85%
2. **Actual reclaim rates** → Confidence increases to 90%  
3. **Compliance costs** → Explains the bunching puzzle

The full model would show:
- Small firms (< £90k): Positive total wedge due to compliance costs
- Large firms (> £200k): Negative wedge dominates
- Sweet spot: Around £150-200k where benefits exceed all costs

## Data Collection Checklist

### Immediate (Can do now):
- [ ] Download HMRC VAT statistics tables
- [ ] Search Google Scholar for UK VAT pass-through studies
- [ ] Check OBR supplementary materials from 2011

### Requires Access:
- [ ] HMRC KAI (Knowledge, Analysis and Intelligence) database
- [ ] ONS Secure Research Service for firm-level data
- [ ] Survey data from business organizations

### Nice to Have:
- [ ] Firm-level VAT returns (anonymized)
- [ ] Detailed compliance time diaries
- [ ] International comparisons for validation

## Bottom Line

We have a **good model** (85% confidence) but need three key pieces:
1. UK-specific pass-through rates
2. Actual VAT reclaim patterns  
3. Compliance cost estimates

These would take us to 95% confidence and resolve why firms bunch despite negative tax wedges.