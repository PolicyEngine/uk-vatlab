# VAT Bunching Analysis

## Overview

This repository implements a comprehensive VAT (Value Added Tax) bunching analysis methodology for analyzing firm responses to VAT registration thresholds, following the approach developed by Liu & Lockwood (2015). The analysis follows the theoretical framework established in the bunching literature and implements a complete pipeline from counterfactual estimation through policy simulation.

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

Following Liu & Lockwood (2015), by grouping companies into small turnover bins of £100, we estimate the counterfactual distribution around the VAT notch $y^*$ using the polynomial regression:

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

- **Saez (2010)**: Foundational bunching estimation methodology for kinked tax schedules
- **Chetty et al. (2011)**: Optimization frictions and adjustment costs in bunching responses  
- **Kleven & Waseem (2013)**: Using notches to uncover optimization frictions and structural elasticities
- **Liu & Lockwood (2015)**: VAT notches analysis providing the core methodology implemented here
- **Best et al. (2018)**: Mortgage notches and intertemporal substitution elasticity estimation
- **Kleven (2016)**: Comprehensive review of bunching methods and applications

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

*Economic Meaning*: **b** is the **bunching ratio** measuring the **excess mass** below the threshold as a fraction of what should be there without the tax.

*Interpretation*:
- **b = 0**: No bunching - tax has no behavioral effect
- **b = 0.1**: 10% excess mass - modest bunching response
- **b = 0.5**: 50% excess mass - strong bunching response
- **b = 1.0**: 100% excess mass - very strong response (twice as many firms as expected)

*Formula logic*:
- **q_N^obs**: **Actual** mass of firms below threshold (what we observe)
- **q_N^cf**: **Expected** mass below threshold without tax distortion
- **Difference**: Excess mass due to bunching behavior
- **Normalization**: Express as fraction of "natural" mass

*Why this matters*:
1. **Policy evaluation**: Quantifies behavioral response to current policy
2. **Cross-country comparison**: Standardized measure of bunching intensity
3. **Theoretical validation**: Links data patterns to underlying economic parameters
4. **Prediction**: Helps forecast responses to policy changes

*Empirical range*: Typical VAT bunching studies find b ∈ [0.05, 0.3], with our baseline estimate b = 0.107 (10.7%) being within normal range.

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

*Economic Meaning*: **τ_e** (tau-e) is the **net effective tax rate** that firms face from VAT registration - the key parameter driving bunching behavior.

*Component breakdown*:
1. **λ(1-ρ)τ**: **Output tax burden** that firm cannot pass through to customers
   - λ: Share of sales to consumers (B2C) - only these sales create real burden
   - (1-ρ): Share of VAT not passed through to customers as higher prices
   - τ: Statutory VAT rate (20% in UK)

2. **τs_c v**: **Input tax credit benefit** from VAT registration
   - τ: VAT rate on inputs
   - s_c: Share of turnover spent on intermediate inputs
   - v: Share of inputs that are VAT-eligible (can claim credits)

*Economic logic*: 
- **If λ(1-ρ)τ > τs_c v**: Net burden from registration → firms bunch below threshold
- **If λ(1-ρ)τ < τs_c v**: Net benefit from registration → firms voluntarily register
- **If λ(1-ρ)τ = τs_c v**: Indifferent → minimal bunching

*Policy implications*: 
- **B2B firms** (low λ): Less bunching due to easier price pass-through
- **Input-intensive firms** (high s_c): Less bunching due to larger input credits
- **Consumer-facing firms** (high λ): More bunching due to price stickiness

*Default calibration*: τ_e = 0.05 (5%) represents a moderate net burden typical for UK firms.

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
- **Method**: Compare observed vs. counterfactual mass ratios in bunching window using CES/logit framework (Kleven & Waseem, 2013)

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

**The CES Derivation (following Kleven & Waseem, 2013):**
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

*Economic Meaning*: This equation describes how the **relative attractiveness** of being above vs below the threshold changes due to the VAT wedge.

*Terms explained*:
- **q_R^obs/q_N^obs**: **Observed ratio** of firms above/below threshold (what we see in data)
- **q_R^cf/q_N^cf**: **Counterfactual ratio** without tax distortions (what ratio "should" be)
- **(1/(1+τ_e))^σ**: **Distortion factor** showing how tax wedge changes relative attractiveness
- **σ**: **Elasticity** controlling strength of response

*Intuition*: 
- **Without tax** (τ_e = 0): Observed ratio = Counterfactual ratio (no distortion)
- **With tax** (τ_e > 0): Observed ratio < Counterfactual ratio (fewer firms above threshold)
- **Higher σ**: Stronger response to same tax wedge
- **Higher τ_e**: Bigger tax penalty, more distortion

*Policy insight*: This equation lets us predict how changing tax parameters (τ_e) will affect firm location choices, given the estimated behavioral elasticity (σ).

**Taking logs:**
```
ln((q_R^obs/q_N^obs)/(q_R^cf/q_N^cf)) = -σ ln(1+τ_e)
```

**Closed-form elasticity calibration:**
```
σ = ln((q_R^cf/q_N^cf)/(q_R^obs/q_N^obs)) / ln(1 + τ_e)
```

*Economic Meaning*: **σ** (sigma) is the **substitution elasticity** measuring how responsive firms are to the VAT registration incentive. It quantifies behavioral flexibility.

*Intuition*: 
- **σ = 0**: Firms completely inflexible - no response to tax incentives
- **σ = 2**: Moderate responsiveness - some firms adjust
- **σ = 5**: High responsiveness - many firms actively avoid threshold
- **σ → ∞**: Perfect flexibility - any tax cost causes complete avoidance

*Formula logic*:
- **Numerator**: How much the above/below ratio changes due to the tax
- **Denominator**: Size of the tax wedge causing the change
- **Ratio**: Responsiveness = (% change in ratio) / (% change in tax cost)

*Why closed-form?*: The CES/logit framework gives us this elegant formula that directly calibrates behavioral responsiveness from observed bunching patterns.

*Policy relevance*: Higher σ means stronger responses to policy changes - more firms will adjust when thresholds or rates change.

### Understanding the Elasticity: Extensive vs Intensive Margins

**Key Question**: The elasticity σ we calibrate - does it capture extensive margin (entry/exit from VAT registration) or intensive margin (adjusting turnover conditional on staying in same regime)?

**Answer**: The VAT bunching elasticity σ is primarily an **EXTENSIVE MARGIN** elasticity, but it captures both margins in a nuanced way.

**Extensive Margin Component (Primary):**
- **Definition**: Choice between two discrete regimes: "VAT-registered" vs "Non-VAT-registered"
- **What σ captures**: **σ measures how firms substitute between two discrete choices: "VAT-registered" vs "Non-VAT-registered"**
- **Behavioral interpretation**: 
  - σ = 0: No firms change registration status regardless of VAT costs
  - σ = ∞: Any VAT cost causes complete exit from registration
- **CES/logit foundation**: σ governs how sensitive the choice between two discrete alternatives is to their relative "prices" (attractiveness)

**Intensive Margin Component (Secondary):**
- **Definition**: Adjusting turnover conditional on chosen regime
- **What σ captures**: Some bunching involves firms reducing their turnover to stay below threshold
- **Mechanism**: Firms may reduce sales, delay invoicing, or restructure operations to control turnover

**Why Both Margins Matter for VAT Bunching:**

**1. Pure Extensive Margin Effects:**
```
Firm naturally at £95k → Chooses to avoid registration → Bunches at £89k
```
- No change in "real" economic activity, just registration choice
- Timing of sales, legal structure changes, etc.

**2. Mixed Extensive-Intensive Effects:**
```
Firm naturally at £95k → Reduces real turnover to £89k to avoid registration
```
- Real reduction in economic scale (intensive margin)
- To achieve extensive margin benefit (avoiding registration)

**Two Policy Parameters, One Underlying Elasticity:**

You correctly identify that there are **two policy parameters**:

**1. Threshold Changes (T* → T*'):**
- Changes the **location** where extensive margin choice becomes relevant
- Same σ governs firm responses, but different firms are now affected
- Step 5 uses: Π' = 1 - (1 + τ_e)^(-σ) with same σ but new threshold location

**2. Tax Rate Changes (τ → τ'):**
- Changes the **intensity** of the effective wedge (τ_e)
- Same σ governs responsiveness, but wedge magnitude changes
- Step 7 uses: σ for revenue elasticity w.r.t rate changes

**The Power of Structural Modeling:**
```
One behavioral parameter σ → Predicts responses to ANY policy change
```

**Empirical Evidence for Extensive vs Intensive:**

**Extensive margin dominance:**
- Most bunching studies find limited evidence of real output reduction
- Firms use timing, legal restructuring, and administrative responses
- Consistent with σ as a "regime-switching" elasticity

**Some intensive margin:**
- Evidence of delayed sales, invoice timing, subcontracting
- But typically smaller magnitude than pure extensive responses

**Policy Implications:**

**For Threshold Changes:**
- σ primarily captures how many firms will switch registration status
- Less about real economic activity changes
- Welfare costs mainly administrative and compliance

**For Rate Changes:**
- σ captures both registration switching AND real activity changes
- Higher rates → both more bunching AND more real distortions
- Larger welfare costs including deadweight losses

**Conclusion:**
The VAT bunching elasticity σ is best interpreted as an **extensive margin elasticity** measuring sensitivity to discrete regime choice, with some intensive margin components. This single parameter allows us to predict responses to both threshold changes (affecting choice location) and rate changes (affecting choice intensity).

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
- **Advanced Implementation**: Sophisticated probabilistic redistribution algorithm extending beyond standard bunching methods

**Mathematical Framework:**

For each firm with observed turnover T^obs ∈ [T* - W, T*]:

**Aggregate displaced share:**
```
Π = 1 - (1 + τ_e)^(-σ)
```

*Economic Meaning*: **Π** represents the fraction of firms in the "above-threshold" region that choose to bunch below the threshold instead of their optimal counterfactual location.

*Intuition*: If Π = 0.18, then 18% of firms that would naturally locate above the threshold T* (in the no-notch world) instead choose to bunch below it to avoid VAT registration. The remaining 82% find VAT registration worthwhile despite the costs.

*Why this formula?*: Comes from the CES/logit choice model. Firms face a choice between "below threshold" (attractive, no VAT) vs "above threshold" (less attractive due to wedge 1+τ_e). The parameter σ controls how sensitive this choice is to the relative attractiveness.

**Local bunching probability:**
```
π(T^obs) = Π × [f^obs(T^obs) - f^cf(T^obs)]_+ / E
```

*Economic Meaning*: **π(T^obs)** is the probability that a firm observed at turnover T^obs is actually a "buncher" (i.e., a firm that moved down from its true optimal location).

*Intuition*: At any observed turnover level T^obs below the threshold, some firms are "locals" (would be there anyway) and some are "bunchers" (moved down from above threshold). This probability tells us the mix.

*Formula breakdown*:
- $[f^{obs} - f^{cf}]_+$: **Excess density** at $T^{obs}$ (how many "extra" firms are there)
- $E$: **Total excess mass** in the bunching region (normalization)
- $\Pi$: **Aggregate displacement rate** (scales the local effect)

*Example*: If π(85k) = 0.3, then 30% of firms observed at £85k turnover are actually bunchers who would optimally be above £90k in the no-notch world.

**Rank among bunchers:**
```
u(T^obs) = ∫[T*-W to T^obs] [f^obs - f^cf]_+ dT / E ∈ [0,1]
```

*Economic Meaning*: **u(T^obs)** gives the "ranking" of a buncher firm observed at T^obs among all bunching firms, from 0 (lowest-productivity buncher) to 1 (highest-productivity buncher).

*Intuition*: Bunchers are heterogeneous - some have low optimal turnover (would be just above threshold), others have high optimal turnover (would be far above threshold). Firms with higher optimal turnover tend to bunch further from the threshold.

*Ranking logic*:
- Firms observed closer to T*-W: **Lower rank** (lower optimal turnover)
- Firms observed closer to T*: **Higher rank** (higher optimal turnover)
- u(T^obs) = 0.2 means this buncher ranks in the bottom 20% by optimal turnover
- u(T^obs) = 0.8 means this buncher ranks in the top 20% by optimal turnover

*Why we need this*: To determine where each buncher should be mapped in the counterfactual distribution - higher-ranked bunchers go to higher turnover locations.

**Deterministic (expected) counterfactual mapping:**
```
E[T^cf|T^obs] = (1 - π(T^obs))T^obs + π(T^obs)(F^cf)^(-1)(F^cf(T*) + u(T^obs)ΔR)
```

*Economic Meaning*: **E[T^cf|T^obs]** is the expected counterfactual turnover for a firm observed at T^obs, accounting for the probability that it might be a buncher.

### Deep Dive: How This Mapping Works

**The Core Economic Problem:**
When we observe a firm at turnover T^obs = £85k (below the £90k threshold), we face uncertainty: Is this firm's "true" optimal location actually £85k, or is it a more productive firm that would naturally be at £95k but is bunching down to avoid VAT?

**The Probabilistic Solution:**
The mapping formula elegantly handles this uncertainty by creating a **mixture model**:

**Component 1: "Local" Firms (Probability 1-π)**
```
(1 - π(T^obs)) × T^obs
```
- These are firms whose **true optimal location** is T^obs
- They would be at £85k even without the VAT threshold
- No displacement needed: T^cf = T^obs = £85k

**Component 2: "Buncher" Firms (Probability π)**
```
π(T^obs) × (F^cf)^(-1)(F^cf(T*) + u(T^obs)ΔR)
```
- These are **displaced firms** whose true optimal location is above the threshold
- The complex term determines WHERE above the threshold they belong

### Detailed Breakdown of the Displacement Target

**Step 1: Start at the threshold in counterfactual CDF**
```
F^cf(T*) = "What fraction of firms should be below £90k in no-notch world"
```

**Step 2: Add ranking adjustment**
```
u(T^obs)ΔR = "How far up the missing mass region this firm should go"
```
- `u(T^obs)` = rank among bunchers (0 to 1)
- `ΔR` = total missing mass above threshold
- **Low-rank buncher** (u ≈ 0): Goes to **bottom** of missing mass region (just above threshold)
- **High-rank buncher** (u ≈ 1): Goes to **top** of missing mass region (far above threshold)

**Step 3: Convert back to turnover level**
```
(F^cf)^(-1)(...) = "Convert CDF value back to actual turnover in £k"
```

### Economic Intuition with Concrete Example

**Firm observed at T^obs = £88k:**
- π(88k) = 0.3 (30% chance it's a buncher)
- u(88k) = 0.7 (if buncher, ranks in top 30% by productivity)

**The mapping gives:**
```
E[T^cf|88k] = 0.7 × £88k + 0.3 × £96k = £61.6k + £28.8k = £90.4k
```

**Interpretation:**
- 70% probability: True optimal location is £88k (local firm)
- 30% probability: True optimal location is £96k (buncher with high productivity)
- **Expected** counterfactual turnover: £90.4k

### Why This Sophisticated Approach?

**1. Heterogeneity Matters:**
Not all bunchers are identical. A firm bunching at £89k likely has higher productivity than one bunching at £80k.

**2. Mass Conservation:**
The algorithm ensures that the total mass moved up from bunching region exactly equals the missing mass above threshold.

**3. Smooth Redistribution:**
Higher-ranked bunchers get mapped to higher locations, creating realistic productivity sorting.

**4. Uncertainty Quantification:**
Rather than making hard assignments ("this firm IS a buncher"), we use probabilistic expectations that reflect our uncertainty.

### Implementation Details

**Rank Calculation:**
```
u_{val} = \frac{\text{cumulative_excess_up_to_}T^{obs}}{\text{total_excess_mass}}
```
- Integrates excess mass from bottom of bunching region up to $T^{obs}$
- Creates smooth ranking based on observed location

**CDF Inversion:**
```
\text{cdf_target} = F^{cf}(T^*) + u_{val} \times \text{missing_mass_share}
```
```
T^{cf}_{displaced} = (F^{cf})^{-1}(\text{cdf_target})
```
- Maps rank to specific location in missing mass region
- Uses interpolation for smooth mapping

**Boundary Handling:**
- Firms outside bunching region: π = 0, so T^cf = T^obs (no change)
- Firms at threshold: Special handling to avoid discontinuities

**Boundary condition:**
If T^obs ∉ [T* - W, T*], set T^cf = T^obs.

**Advanced Probabilistic Mapping Implementation:**
Uses sophisticated redistribution algorithm with optimization to achieve smooth counterfactual distribution across the full range.

### Step 5: Forward Mapping to New Policy

- **Objective**: Simulate firm responses under alternative VAT thresholds by creating bunching at a new threshold location
- **Pipeline**: Real (£90k) → Counterfactual (no notch) → New Policy (£100k)
- **Method**: Reverse the Step 4 mapping to redistribute firms and create bunching at the new threshold

**Economic Intuition:**

Step 5 answers the policy question: **"What would happen to firm behavior if we moved the VAT threshold from £90k to £100k?"**

The three-stage pipeline works as follows:
1. **Real World (£90k)**: Observed distribution with bunching at current threshold
2. **No-Notch Counterfactual**: What the distribution would look like without any VAT threshold (from Step 1)
3. **New Policy (£100k)**: What the distribution would look like with bunching at the new threshold location

**Why This Approach Works:**
By going through the counterfactual "no-notch" world, we separate the **structural behavioral parameters** (elasticity σ) from the **policy parameters** (threshold location, wedge size). This allows us to simulate any policy change using the same underlying firm responsiveness.

**Mathematical Framework:**

**Step 5a: Compute New Policy Parameters**

**New effective wedge (if different):**
```
τ'_e = λ(1-ρ)τ' - τ's_cv  (or use same as original: τ'_e = τ_e)
```

*Intuition*: The effective wedge may change if the VAT rate changes, but for threshold-only reforms, we typically use the same wedge.

**New displaced share under new wedge:**
```
Π' = 1 - (1 + τ'_e)^(-σ)
```

*Economic Meaning*: **Π'** is the fraction of firms that would optimally locate above the new threshold T*' but choose to bunch below it instead. This is the "aggregate displaced share" under the new policy.

*Intuition*: If Π' = 0.2, then 20% of firms near the new threshold will bunch below it rather than locate above it. Higher σ (more elastic firms) leads to higher Π' (more bunching).

**Step 5b: Redistribute Mass to Create New Bunching**

The algorithm takes the smooth counterfactual distribution f^cf and redistributes firm mass to create bunching at the new threshold T*'.

**Mass redistribution principle:**
```
Mass above new threshold in counterfactual × Π' = Mass that moves down to create bunching
```

**Implementation Details:**

1. **Identify source region**: Firms above new threshold T*' in counterfactual
2. **Calculate mass to move**: $\text{mass_to_move} = \Pi' \times \text{mass_above_new_threshold}$
3. **Reduce density above threshold**: $f_{new}[\text{above } T^{*'}] = f^{cf}[\text{above } T^{*'}] \times (1 - \Pi')$
4. **Increase density below threshold**: Redistribute moved mass to region below T*'
5. **Apply sophisticated smoothing**: Multiple passes of moving averages to eliminate artificial discontinuities

**Distance-based redistribution weights:**
The moved mass is distributed below the new threshold using inverse-distance weighting:
```
weights = 1 / max(T*' - T, 0.5) for T < T*'
```

*Intuition*: Firms bunch closer to the threshold, so bins immediately below T*' receive more of the redistributed mass.

**Step 5c: Quality Assurance Features**

**Mass conservation check:**
```
∫ f_new(T) dT = ∫ f_cf(T) dT
```
*Ensures total number of firms remains constant*

**Smoothing algorithm:**
- **3-point moving average**: $0.25 \times f[i-1] + 0.5 \times f[i] + 0.25 \times f[i+1]$
- **5-point moving average**: $0.1 \times f[i-2] + 0.2 \times f[i-1] + 0.4 \times f[i] + 0.2 \times f[i+1] + 0.1 \times f[i+2]$
- **11-point Gaussian**: Final smoothing with Gaussian-like weights

*Purpose*: Eliminate sharp discontinuities that would be unrealistic in real firm data.

**Step 5d: Asymmetric Window Support**

The implementation supports different window sizes for the new policy:
```python
# Different windows around new £100k threshold
new_policy_window_left = 25   # £25k below (£75k-£100k)
new_policy_window_right = 20  # £20k above (£100k-£120k)
```

*Flexibility*: Allows fine-tuning of the analysis region around the new threshold based on economic considerations.

**Economic Output:**

Step 5 produces:
1. **f_new_policy**: New firm turnover distribution with bunching at T*'
2. **Bunching statistics**: Excess mass, missing mass around new threshold
3. **Policy comparison metrics**: Changes in firm behavior patterns
4. **Visual verification**: New bunching spike at T*' = £100k in the purple curve

**Policy Insights:**

- **Threshold increase effects**: Moving from £90k to £100k reduces the number of affected firms (fewer firms near £100k than £90k)
- **Revenue implications**: Can be analyzed in Step 6 using the new distribution
- **Behavioral consistency**: Same elasticity σ governs responses at both thresholds
- **Welfare effects**: Deadweight loss patterns shift with the threshold location

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

**Revenue formula for each firm (following Liu & Lockwood, 2015):**
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
V_{total}^{old} = \sum_i V_i^{old} = \sum_i \tau_{old}(\theta T_i^{old} - vs_c T_i^{old})
```
```  
V_{total}^{new} = \sum_i V_i^{new} = \sum_i \tau_{new}(\theta T_i^{new} - vs_c T_i^{new})
```

**Revenue change:**
```
\Delta V = V_{total}^{new} - V_{total}^{old}
```
```
\Delta V\% = 100 \times \frac{\Delta V}{V_{total}^{old}}
```

**Step 7: Elasticity Calculations**

**1) Behavioral (odds) elasticity (following Kleven, 2016):**
```
ε_{behavioral} = -σ = \frac{d \ln(q_R/q_N)}{d \ln(1+τ_e)}
```

**2) Revenue elasticity w.r.t VAT rate:**
```
\varepsilon_{revenue}^{rate} = \frac{dV/d\tau \times \tau/V}{1} = \frac{dV/V}{d\tau/\tau}
```

Using finite differences:
```
\frac{dV}{d\tau} \approx \frac{V(\tau+\varepsilon) - V(\tau-\varepsilon)}{2\varepsilon}
```

**3) Revenue elasticity w.r.t threshold:**
```
\varepsilon_{revenue}^{threshold} = \frac{dV/dT^* \times T^*}{V}
```

Where $T^*$ is the VAT registration threshold.

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