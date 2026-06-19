# Understanding the VAT Threshold Notch and Revenue Effects

## What is a VAT Notch?

A "notch" in tax policy is a **discontinuous jump** in tax liability at a specific threshold. The UK VAT system creates one of the most significant notches in the tax system.

### The Discontinuity

**Below £90,000 turnover:**
- No VAT registration required
- Keep 100% of sales revenue
- No VAT compliance costs

**At £90,001 turnover:**
- Must register for VAT
- Charge 20% VAT on ALL sales (not just the amount above £90k)
- Face compliance costs (filing, accounting)

## Revenue Impact Example

Let's compare two similar businesses:

### Business A: £89,999 turnover
- VAT paid: £0
- Net income: £89,999

### Business B: £90,001 turnover
- Must charge 20% VAT on all sales
- If they can't pass VAT to customers: effective income drops
- If customers are VAT-registered businesses: less impact
- If customers are consumers: 20% price increase or margin squeeze

## How the Notch Affects Government Revenue

### 1. Direct Effect (Mechanical)
Without any behavioral response, adding firms above threshold increases revenue:
- Each firm above £90k contributes VAT
- Revenue = (Turnover × VAT rate × Value-added ratio)
- Example: £100k turnover × 20% × 50% value-added = £10k VAT

### 2. Behavioral Response (What Actually Happens)

#### Bunching Below Threshold
Firms deliberately limit growth to stay below £90k:
- **Lost VAT revenue**: Firms that would naturally grow above £90k stay below
- **Lost economic output**: Real economic activity is suppressed

#### Growth Slowdown
Firms near but above threshold grow more slowly:
- **Elasticity effect**: 0.14 elasticity means 14% reduction in turnover per 100% tax increase
- **With 20% VAT**: Turnover reduces by ~2.8% (0.14 × 0.20)

### 3. Revenue Calculation in Our Model

```
Total VAT Revenue = Σ(Registered Firms) × [Turnover × Value-Added Ratio × VAT Rate]

Where:
- Registered Firms = Firms with turnover ≥ £90k (after behavioral response)
- Value-Added Ratio ≈ 50% (assumption: half of turnover is value-added)
- VAT Rate = 20%
```

### 4. Why Revenue Changes with Different Thresholds

#### Lower Threshold (£85k instead of £90k):
**Gains:**
- +5,000 more firms must register
- Each contributes ~£8.5k-£9k VAT annually
- Total gain: ~£40-45M

**Losses:**
- More bunching (distortion increases)
- Larger behavioral response
- Some firms reduce activity more

**Net effect:** Usually positive but with higher economic distortion

#### Higher Threshold (£100k instead of £90k):
**Gains:**
- Less bunching/distortion
- Firms grow more naturally
- Higher productivity

**Losses:**
- Fewer registered firms
- Lost revenue from £90k-£100k firms

**Net effect:** Lower revenue but healthier economy

## The Marginal Rates Solution

Instead of a sharp notch, gradual rates could help:

```
Turnover          VAT Rate
£0-£30k          0%
£30k-£60k        10% (voluntary)
£60k-£90k        15% (voluntary)
£90k+            20% (mandatory)
```

This would:
- Reduce bunching incentive
- Allow gradual transition
- Maintain revenue through voluntary registration
- Reduce economic distortion

## Key Insight: The Trade-off

The VAT threshold creates a fundamental trade-off:
1. **Lower threshold** → More revenue but more distortion
2. **Higher threshold** → Less distortion but less revenue
3. **Current £90k** → Significant bunching (~1,500 firms in our simulation)

The behavioral response costs the UK government approximately:
- **£50-100M annually** in lost revenue (our simulation estimate)
- **£350M in lost economic output** (OBR estimate for firms capping growth)

This is why economists often advocate for either:
- Very high thresholds (minimize distortion)
- Very low thresholds (minimize bunching opportunity)
- Graduated/marginal systems (smooth the transition)