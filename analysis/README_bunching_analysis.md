# VAT Bunching Analysis

## Overview

This repository implements a comprehensive VAT (Value Added Tax) bunching analysis methodology for analyzing firm responses to VAT registration thresholds. The analysis follows the theoretical framework established in the bunching literature and implements a complete pipeline from counterfactual estimation through policy simulation.

## Background

VAT registration thresholds create economic incentives for firms to "bunch" just below the threshold to avoid mandatory registration. This bunching behavior provides insights into:

- **Behavioral elasticities**: How responsive firms are to tax incentives
- **Policy effectiveness**: The impact of threshold changes on firm behavior and revenue

### Theoretical Foundation

The VAT registration threshold at the cutoff turnover value y* induces excess bunching by companies for which voluntary registration is not optimal. The bunching is driven by the productivity parameter and generates an excess mass by companies who would have reported turnover between y* and y* + Δy* absent the notch:

**Excess bunching formula:**
```
B(y*) = ∫[y* to y*+Δy*] g(y)dy ≈ g(y*)Δy*
```

Where:
- B(y*) = excess mass at the threshold
- g(y) = counterfactual density distribution of turnover without registration threshold
- The approximation is accurate when g(y) is uniform around the notch

### Empirical Estimation Framework

By grouping companies into small turnover bins of £100, we estimate the counterfactual distribution around the VAT notch y* using the regression:

**Counterfactual regression:**
```
c_j = Σ[l=0 to q] β_l(y_j)^l + Σ[i=y*- to y*+] γ_i I{j = i} + ε_j
```

Where:
- c_j = number of companies in turnover bin j
- y_j = distance between turnover bin j and the VAT notch y*
- q = order of the polynomial
- I{·} = indicator function
- [y*-, y*+] = turnover bins around notch excluded from regression

**Excess bunching estimation:**
```
B̂ = Σ[i=y*- to y*] (c_j - ĉ_j)
```

**Bunching ratio:**
```
b(y*) = B(y*)/g(y*) ≈ Δy*/y*
```

This ratio denotes the fraction of companies that bunch at the notch relative to the counterfactual density and approximates the relative response under no optimization frictions.

The methodology implemented here builds on the seminal work in the bunching literature, particularly:

- **Saez (2010)**: Foundational bunching estimation methodology
- **Chetty et al. (2011)**: Optimization frictions and adjustment costs in bunching
- **Kleven et al. (2013)**: VAT notches and firm responses
- **Best et al. (2018)**: Mortgage notches and intertemporal substitution elasticity
- **Liu & Lockwood (2015)**: VAT notches analysis (CESifo Working Paper 5371)
- **Kleven (2016)**: Comprehensive review of bunching methods (Annual Review of Economics)

## Methodology

The analysis implements a **5-step pipeline** for VAT bunching analysis:

### Step 1: Counterfactual Distribution and Bunching Statistics

- **Objective**: Build a smooth counterfactual distribution representing firm turnover without the VAT threshold
- **Method**: Polynomial regression excluding the bunching region [T* - W, T* + W]

**Mathematical Framework:**

Pick a window W around the threshold T* (e.g. W = £10k).

Fit the counterfactual density f^cf(T) excluding [T* - W, T* + W] and predict inside.

Bin the observed data to get f^obs(T) and CDFs F^obs, F^cf.

**Masses in the window:**
```
q_N^obs = ∫[T*-W to T*] f^obs(T)dT,    q_R^obs = ∫[T* to T*+W] f^obs(T)dT

q_N^cf = ∫[T*-W to T*] f^cf(T)dT,      q_R^cf = ∫[T* to T*+W] f^cf(T)dT
```

**Excess & missing mass:**
```
E = ∫[T*-W to T*] [f^obs - f^cf]_+ dT,    ΔR = ∫[T* to T*+W] [f^cf - f^obs]_+ dT
```

**Bunching ratio:**
```
b = (q_N^obs - q_N^cf) / q_N^cf
```

### Step 2: Effective Wedge Calibration

- **Objective**: Quantify the effective tax burden from VAT registration

**Economic Intuition:**

The effective wedge captures the **two channels** firms care about when deciding whether VAT registration is costly:

**What changes when a firm registers for VAT?**

1. It must **charge VAT on outputs** (sales)
2. It can **reclaim VAT on inputs** (intermediate purchases)

So the **net effective wedge** is:
```
τ_e = (extra output VAT burden not passed on) - (input VAT credit benefit)
```

**Step-by-step construction:**

**The output side:**
- Statutory VAT rate: τ
- Share λ of sales is to **consumers** (B2C) - business customers reclaim VAT, so they don't care
- Of that VAT, share ρ is **passed through** into higher consumer prices
  - If ρ = 1: firm shifts whole burden to customers
  - If ρ = 0: firm absorbs it all

**Effective output VAT cost to the firm:**
```
λ(1-ρ)τ
```

**The input side:**
- Input costs = s_c share of turnover
- Share v of those inputs are VAT-eligible  
- When registered, firm can reclaim VAT on those inputs, getting a saving of:
```
τ · s_c · v
```

**Mathematical Framework:**

**Net effective wedge formula:**
```
τ_e = λ(1-ρ)τ - τs_c v
```

Where:
- τ = VAT rate
- λ = B2C sales share  
- ρ = price pass-through rate
- s_c = input cost share
- v = VAT-eligible input share

**Interpretation:**
- If **output term dominates** → τ_e > 0: firms want to stay below threshold (classic bunching)
- If **input term dominates** → τ_e < 0: firms prefer registration (explains voluntary registration)

**Default**: τ_e = 0.050 (5% effective wedge assumption)

This formula is a **simple accounting-based wedge** constructed by:
1. Taking the **output VAT firms can't shift** to customers
2. Subtracting the **input VAT credits they gain** from registration

### Step 3: Substitution Elasticity Estimation

- **Objective**: Calibrate behavioral responsiveness using CES/logit framework
- **Method**: Compare observed vs. counterfactual mass ratios in bunching window

**Economic Intuition:**

**The Economic Problem:**
Firms around the VAT threshold face a binary choice:
- **Regime N**: Stay below threshold → turnover T < T*, avoid VAT
- **Regime R**: Go above threshold → turnover T ≥ T*, register for VAT, face effective wedge 1+τ_e

From the firm's perspective, "being above" and "being below" are like **two alternative production states**, and the VAT wedge changes their relative attractiveness.

**Why CES/logit?**
Economists model **choice between two options** with CES or multinomial logit because:
- CES aggregators produce **constant elasticity of substitution** across alternatives
- **Parsimonious**: one parameter σ summarizes how sensitive the ratio of choices is to relative "price" changes
- Nests intuitive extremes:
  - σ = 0: firms never switch regimes, regardless of wedge
  - σ → ∞: firms infinitely responsive, any wedge fully empties one regime

**The CES Derivation:**
Start with CES utility (or profit "attractiveness") over two "varieties":
```
U = [(q_N^cf)^((σ-1)/σ) + (q_R^cf/(1+τ_e))^((σ-1)/σ)]^(σ/(σ-1))
```

Where:
- q_N^cf, q_R^cf are counterfactual attractiveness levels (red line masses)
- The wedge 1+τ_e acts like a relative price penalty on the "above" option

**CES demand system implies:**
```
q_R^obs/q_N^obs = (1/(1+τ_e))^σ × q_R^cf/q_N^cf
```

**Logit Equivalence:**
If firms make **probabilistic choices** with random taste shocks (McFadden logit):
```
q_R^obs/q_N^obs = exp(-σ ln(1+τ_e)) × q_R^cf/q_N^cf
```

Same reduced form as CES.

**Mathematical Framework:**

**CES/logit share equation:**
```
q_R^obs/q_N^obs = (1/(1+τ_e))^σ × q_R^cf/q_N^cf
```

**Taking logs:**
```
ln((q_R^obs/q_N^obs)/(q_R^cf/q_N^cf)) = -σ ln(1+τ_e)
```

**Closed-form elasticity calibration:**
```
σ = ln((q_R^cf/q_N^cf)/(q_R^obs/q_N^obs)) / ln(1 + τ_e)
```

**Intuition:**
- Counterfactual ratio q_R^cf/q_N^cf: what "red line" says above:below balance should be
- Observed ratio q_R^obs/q_N^obs: smaller because firms bunch below
- Wedge 1+τ_e: "relative price" penalty of being above  
- σ: how strongly penalty pulls mass downward
  - Bigger drop in ratio given wedge → larger σ
  - If no drop (obs = cf), then σ = 0

**Why this works for VAT threshold bunching:**
- **Links micro bunching behavior to single calibratable parameter**
- **Enables policy simulation**: predict how above:below ratio shifts with reforms
- **Strong economic pedigree**: CES/logit substitution is workhorse in trade models, demand estimation, discrete choice, and optimal tax bunching

**Interpretation**: Higher σ = more elastic firm responses to tax incentives

### Step 4: Micro-Level Mapping to No-Notch World

- **Objective**: Create individual firm mappings from observed to counterfactual turnover
- **Advanced Implementation**: Sophisticated probabilistic redistribution algorithm

**Mathematical Framework:**

For each firm with observed turnover T^obs ∈ [T* - W, T*]:

**Aggregate displaced share:**
```
Π = 1 - (1 + τ_e)^(-σ)
```

**Local bunching probability:**
```
π(T^obs) = Π × [f^obs(T^obs) - f^cf(T^obs)]_+ / E
```

**Rank among bunchers:**
```
u(T^obs) = ∫[T*-W to T^obs] [f^obs - f^cf]_+ dT / E ∈ [0,1]
```

**Deterministic (expected) counterfactual mapping:**
```
E[T^cf|T^obs] = (1 - π(T^obs))T^obs + π(T^obs)(F^cf)^(-1)(F^cf(T*) + u(T^obs)ΔR)
```

**Boundary condition:**
If T^obs ∉ [T* - W, T*], set T^cf = T^obs.

**Advanced Probabilistic Mapping Implementation:**
Uses sophisticated redistribution algorithm with optimization to achieve smooth counterfactual distribution across the full range.

### Step 5: Forward Mapping to New Policy

- **Objective**: Simulate firm responses under alternative VAT thresholds
- **Pipeline**: Real (£90k) → Counterfactual (no notch) → New Policy (£100k)
- **Method**: Reverse the Step 4 mapping to create bunching at new threshold

**Mathematical Framework:**

Complete pipeline: Real (£90k) → Counterfactual (no notch) → New Policy (£100k)

**New wedge:**
```
τ'_e = λ(1-ρ)τ' - τ's_cv  (or treat as given)
```

**Displaced share under new wedge:**
```
Π' = 1 - (1 + τ'_e)^(-σ)
```

**Recenter the same no-notch density f^cf at T*'**

**Reverse mapping from T^cf to new observed T^new near T*':**

**Local move-down probability:**
```
π'(T^cf) = Π' × f^cf(T^cf) / ∫[T*' to T*'+W] f^cf(t)dt
```

**Rank above new threshold:**
```
v(T^cf) = ∫[T*' to T^cf] f^cf(t)dt / ∫[T*' to T*'+W] f^cf(t)dt
```

**Expected new observed turnover:**
```
E[T^new|T^cf] = (1 - π'(T^cf))T^cf + π'(T^cf)(F^cf)^(-1)(F^cf(T*) - v(T^cf)E')
```

where E' = Π' ∫[T*' to T*'+W] f^cf(t)dt is the target excess below new threshold.

**Features**: Smoothing algorithms to eliminate sharp transitions

## Key Features

### Advanced Probabilistic Mapping

The implementation uses an advanced probabilistic mapping approach that:

- **Preserves mass conservation**: Total firm count remains constant
- **Creates smooth distributions**: Eliminates artificial discontinuities
- **Optimizes parameters**: Uses scipy optimization for best fit
- **Handles full range**: Maps firms across entire turnover distribution

### Asymmetric Windows

Supports different window sizes on each side of thresholds:

```python
# Counterfactual estimation windows
counterfactual_window_left = 25   # £25k below £90k threshold
counterfactual_window_right = 20  # £20k above £90k threshold

# New policy windows  
new_policy_window_left = 25       # £25k below £100k threshold
new_policy_window_right = 20      # £20k above £100k threshold
```

## Usage

### Basic Usage

```python
from bunching_analysis import CounterfactualBunchingAnalysis

# Initialize analysis
analysis = CounterfactualBunchingAnalysis(
    threshold=90,                    # £90k VAT threshold
    window_left=25,                  # Analysis window parameters
    window_right=20,
    new_policy_window_left=25,
    new_policy_window_right=20
)

# Run complete pipeline
results = analysis.run_complete_analysis()
```

### Advanced Configuration

```python
# Custom effective wedge and elasticity
analysis.set_effective_wedge(0.045)  # 4.5% effective wedge
analysis.calibrate_substitution_elasticity()

# Run Step 4 advanced mapping
analysis.run_step4_analysis()

# Forward map to new policy
analysis.step5_forward_map_to_new_policy(T_star_new=100)
```

## Results

### Baseline Results (£90k threshold)

- **Bunching ratio**: `b = 0.107` (10.7% excess mass)
- **Effective wedge**: `τ_e = 0.050` (5%)
- **Substitution elasticity**: `σ = 4.117`
- **Displaced share**: `Π = 0.182` (18.2%)

### Policy Simulation (£90k → £100k)

- Successfully creates new bunching at £100k
- Removes bunching at original £90k threshold
- Smooth transition with minimal artificial effects
- Revenue and elasticity analysis included

## Evidence from Literature

### Empirical Findings

The methodology replicates key findings from the VAT bunching literature:

1. **Sharp bunching below threshold**: Consistent with theoretical predictions
2. **Missing mass above threshold**: Evidence of real behavioral responses
3. **Heterogeneity by firm characteristics**:
   - Higher bunching for B2C-focused firms
   - Lower bunching for input-intensive firms
4. **Policy tracking**: Bunching follows threshold changes over time

### Robustness Checks

- **Polynomial order sensitivity**: Results stable across specifications
- **Window size robustness**: Consistent estimates across reasonable windows
- **Mass conservation**: Advanced mapping preserves total firm count
- **Smoothness**: Counterfactual distributions are economically plausible

## Extensions

### Steps 6-7: Revenue and Elasticity Analysis

The production version includes:

**Step 6: Revenue Mapping Analysis**

**Revenue formula for each firm:**
```
V = τ(θT - vs_cT)
```

Where:
- V = VAT revenue per firm
- τ = VAT rate (20% in UK)
- θ = taxable output share (typically 85%)
- T = firm turnover
- v = VAT-eligible input share (typically 70%)
- s_c = input cost share (typically 45%)

**Aggregate revenue calculation:**
```
V_total^old = Σ_i V_i^old = Σ_i τ_old(θT_i^old - vs_cT_i^old)
V_total^new = Σ_i V_i^new = Σ_i τ_new(θT_i^new - vs_cT_i^new)
```

**Revenue change:**
```
ΔV = V_total^new - V_total^old
ΔV% = 100 × ΔV / V_total^old
```

**Step 7: Elasticity Calculations**

**1) Behavioral (odds) elasticity:**
```
ε_behavioral = -σ = d ln(q_R/q_N) / d ln(1+τ_e)
```

**2) Revenue elasticity w.r.t VAT rate:**
```
ε_revenue^rate = (dV/dτ) × (τ/V) = (dV/V) / (dτ/τ)
```

Using finite differences:
```
dV/dτ ≈ (V(τ+ε) - V(τ-ε)) / (2ε)
```

**3) Revenue elasticity w.r.t threshold:**
```
ε_revenue^threshold = (dV/dT*) × (T*/V)
```

Where T* is the VAT registration threshold.

- Comprehensive parameter assumptions for UK firms based on HMRC data and academic literature

### Potential Extensions

- **Sector-specific analysis**: Industry heterogeneity in responses
- **Dynamic analysis**: Multi-period bunching patterns
- **Welfare calculations**: Deadweight loss from tax-induced distortions
- **Machine learning**: Non-parametric counterfactual estimation

## References

1. **Saez, E.** (2010). "Do taxpayers bunch at kink points?" *American Economic Journal: Economic Policy*, 2(3), 180-212.

2. **Chetty, R., Friedman, J. N., Olsen, T., & Pistaferri, L.** (2011). "Adjustment costs, firm responses, and micro vs. macro labor supply elasticities." *Quarterly Journal of Economics*, 126(2), 749-804.

3. **Kleven, H. J., & Waseem, M.** (2013). "Using notches to uncover optimization frictions and structural elasticities." *Quarterly Journal of Economics*, 128(2), 669-723.

4. **Best, M. C., Cloyne, J., Ilzetzki, E., & Kleven, H. J.** (2018). "Estimating the elasticity of intertemporal substitution using mortgage notches." *NBER Working Paper 24948*.

5. **Liu, L., & Lockwood, B.** (2015). "VAT notches." *CESifo Working Paper Series No. 5371*.

6. **Kleven, H. J.** (2016). "Bunching." *Annual Review of Economics*, 8(1), 435-464.