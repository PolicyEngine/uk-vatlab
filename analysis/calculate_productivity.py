"""
Calculate firm productivity and returns to scale parameter (alpha)
Using firms below VAT threshold to avoid distortion
"""

import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv('/Users/janansadeqian/PolicyEngine_VATLab/analysis/synthetic_firms_turnover.csv')

print("=" * 60)
print("FIRM PRODUCTIVITY AND RETURNS TO SCALE CALCULATION")
print("=" * 60)
print(f"\nTotal firms: {df['weight'].sum():,.0f}")

# Convert turnover and input from thousands to actual values
df['turnover'] = df['annual_turnover_k'] * 1000
df['input'] = df['annual_input_k'] * 1000

# Define VAT threshold and bunching region
VAT_THRESHOLD = 85000  # Correct UK VAT threshold
EXCLUDE_LOWER = 75000  # Exclude firms in [75k-85k] and [85k-95k] regions
EXCLUDE_MIDDLE = 95000

# Identify firms excluding the distortion region around threshold
# Include firms below £75k AND above £95k (exclude only the [75k-95k] region)
estimation_firms = df[(df['turnover'] < EXCLUDE_LOWER) | (df['turnover'] > EXCLUDE_MIDDLE)].copy()

below_75k = df[df['turnover'] < EXCLUDE_LOWER]
above_95k = df[df['turnover'] > EXCLUDE_MIDDLE]

print(f"\nFirms below £75k: {below_75k['weight'].sum():,.0f}")
print(f"Firms above £95k: {above_95k['weight'].sum():,.0f}")
print(f"Total for estimation: {estimation_firms['weight'].sum():,.0f}")
print(f"Percentage: {estimation_firms['weight'].sum() / df['weight'].sum() * 100:.1f}%")

# Show what we're excluding
excluded_region = df[(df['turnover'] >= EXCLUDE_LOWER) & (df['turnover'] <= EXCLUDE_MIDDLE)]
print(f"Excluded firms (£75-95k): {excluded_region['weight'].sum():,.0f}")

# Also identify the actual bunching region
bunching_region = df[(df['turnover'] >= 80000) & (df['turnover'] <= 85000)]
print(f"Bunching firms (£80-85k): {bunching_region['weight'].sum():,.0f}")

# Step 1: Estimate alpha (returns to scale parameter)
print("\n" + "=" * 60)
print("STEP 1: ESTIMATE RETURNS TO SCALE (α)")
print("=" * 60)

# Remove firms with zero or negative inputs/outputs for log calculation
valid_firms = estimation_firms[(estimation_firms['turnover'] > 0) & 
                               (estimation_firms['input'] > 0)].copy()

print(f"\nFirms for estimation: {valid_firms['weight'].sum():,.0f}")

# Debug: Check what's being removed
removed_zero = estimation_firms[(estimation_firms['turnover'] <= 0) | 
                                (estimation_firms['input'] <= 0)]
print(f"Removed firms (zero/negative values): {removed_zero['weight'].sum():,.0f}")

print(f"\nData check:")
print(f"  Total estimation pool: {estimation_firms['weight'].sum():,.0f}")
print(f"  Valid for logs: {valid_firms['weight'].sum():,.0f}")
print(f"  Zero/negative removed: {estimation_firms['weight'].sum() - valid_firms['weight'].sum():,.0f}")

# Calculate log values
valid_firms['ln_Y'] = np.log(valid_firms['turnover'])
valid_firms['ln_X'] = np.log(valid_firms['input'])

# Calculate weighted covariance and variance
# Calculate means
mean_ln_Y = np.average(valid_firms['ln_Y'], weights=valid_firms['weight'])
mean_ln_X = np.average(valid_firms['ln_X'], weights=valid_firms['weight'])

# Calculate covariance and variance
cov_xy = np.average(
    (valid_firms['ln_Y'] - mean_ln_Y) * (valid_firms['ln_X'] - mean_ln_X),
    weights=valid_firms['weight']
)

var_x = np.average(
    (valid_firms['ln_X'] - mean_ln_X) ** 2,
    weights=valid_firms['weight']
)

# Calculate alpha
alpha = cov_xy / var_x

print(f"\nCov(ln Y, ln X): {cov_xy:.4f}")
print(f"Var(ln X): {var_x:.4f}")
print(f"\n*** ESTIMATED α = {alpha:.4f} ***")

# Verify with OLS regression
from sklearn.linear_model import LinearRegression

model = LinearRegression()
X_reg = valid_firms['ln_X'].values.reshape(-1, 1)
y_reg = valid_firms['ln_Y'].values
weights_reg = valid_firms['weight'].values

model.fit(X_reg, y_reg, sample_weight=weights_reg)
alpha_ols = model.coef_[0]

print(f"OLS estimate: α = {alpha_ols:.4f}")
print(f"R-squared: {model.score(X_reg, y_reg, sample_weight=weights_reg):.4f}")

# Step 2: Calculate firm productivity A_i for ALL firms
print("\n" + "=" * 60)
print("STEP 2: CALCULATE FIRM PRODUCTIVITY (A_i)")
print("=" * 60)

# Apply to all firms with valid data
all_valid = df[(df['turnover'] > 0) & (df['input'] > 0)].copy()
all_valid['productivity'] = all_valid['turnover'] / (all_valid['input'] ** alpha)

print(f"\nCalculating productivity for {all_valid['weight'].sum():,.0f} firms")

# Summary statistics
prod_mean = np.average(all_valid['productivity'], weights=all_valid['weight'])
prod_std = np.sqrt(np.average((all_valid['productivity'] - prod_mean) ** 2, 
                              weights=all_valid['weight']))

print(f"\nProductivity Statistics (A_i):")
print(f"  Mean: {prod_mean:.2f}")
print(f"  Std Dev: {prod_std:.2f}")
print(f"  Min: {all_valid['productivity'].min():.2f}")
print(f"  Max: {all_valid['productivity'].max():.2f}")

# Check productivity by firm size
print("\n" + "=" * 60)
print("PRODUCTIVITY BY FIRM SIZE")
print("=" * 60)

# Create turnover bins
bins = [0, 30000, 60000, 90000, 150000, np.inf]
labels = ['<£30k', '£30-60k', '£60-90k', '£90-150k', '>£150k']
all_valid['size_bin'] = pd.cut(all_valid['turnover'], bins=bins, labels=labels)

for bin_label in labels:
    bin_firms = all_valid[all_valid['size_bin'] == bin_label]
    if len(bin_firms) > 0:
        bin_prod = np.average(bin_firms['productivity'], weights=bin_firms['weight'])
        bin_count = bin_firms['weight'].sum()
        print(f"  {bin_label:12s}: A = {bin_prod:6.2f} ({bin_count:7.0f} firms)")

# Check bunching region specifically
print("\n" + "=" * 60)
print("BUNCHING REGION ANALYSIS")
print("=" * 60)

bunching_firms = all_valid[(all_valid['turnover'] >= 80000) & 
                           (all_valid['turnover'] <= 85000)]

if len(bunching_firms) > 0:
    bunch_prod = np.average(bunching_firms['productivity'], 
                           weights=bunching_firms['weight'])
    print(f"\nFirms in bunching region (£80-85k):")
    print(f"  Firms: {bunching_firms['weight'].sum():,.0f}")
    print(f"  Average productivity: {bunch_prod:.2f}")
    
    # Show productivity distribution for bunching firms
    print(f"\n  Productivity range for bunchers:")
    print(f"    Min A_i: {bunching_firms['productivity'].min():.2f}")
    print(f"    Max A_i: {bunching_firms['productivity'].max():.2f}")
    print(f"    This will determine counterfactual output range")

# Save results
print("\n" + "=" * 60)
print("SAVING RESULTS")
print("=" * 60)

# Add productivity to original dataframe
df['productivity'] = df['turnover'] / (df['input'] ** alpha)

# Save enhanced dataset
output_file = 'synthetic_firms_with_productivity.csv'
df.to_csv(output_file, index=False)
print(f"\nSaved enhanced dataset to: {output_file}")

# Save parameters
params = {
    'alpha': alpha,
    'vat_threshold': VAT_THRESHOLD,
    'mean_productivity': prod_mean,
    'std_productivity': prod_std
}

import json
with open('calibrated_parameters.json', 'w') as f:
    json.dump(params, f, indent=2)
print(f"Saved parameters to: calibrated_parameters.json")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\nKey calibrated parameters:")
print(f"  α (returns to scale) = {alpha:.4f}")
print(f"  Mean productivity = {prod_mean:.2f}")
print(f"\nThese parameters will be used for policy simulation")