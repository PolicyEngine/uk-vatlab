"""
Reverse Productivity Estimation from FOC
========================================
Given actual turnover as "optimal y", solve for A_i (productivity) using FOC equation:

1 - τ_max/(1 + e^(-k(y_i* - T*))) = (1/α) · (1/A_i^(1/α)) · (y_i*)^((1-α)/α) + (k · τ_max · e^(-k(y_i* - T*)))/(1 + e^(-k(y_i* - T*)))^2
"""

import numpy as np
import pandas as pd
from scipy.optimize import fsolve
import warnings
warnings.filterwarnings('ignore')

print("=== Reverse Productivity Estimation ===")

# Load data
print("\n1. Loading data...")
df = pd.read_csv('synthetic_firms_with_productivity.csv')
print(f"   ✓ Loaded {len(df):,} firms")

# Use all data for full analysis
print(f"   ✓ Using all data: {len(df):,} firms")
print(f"   ✓ Total weighted firms: {df['weight'].sum():,.0f}")

# Parameters from current tax system
alpha = 0.9864
tau_max = 0.20
T_star = 85000
k = 0.01  # Moderately sharp sigmoid transition

print(f"\nTax system parameters:")
print(f"   α (elasticity): {alpha}")
print(f"   τ_max (VAT rate): {tau_max}")
print(f"   T* (threshold): £{T_star:,}")
print(f"   k (sigmoid steepness): {k}")

def solve_for_productivity(y_optimal, gamma=0.1, sigma_sq=0.01):
    """
    Given y_optimal (actual turnover), solve for A_i using FOC equation with uncertainty:
    
    1 - τ_max/(1 + e^(-k(y* - T*))) = (1/α) · (1/A_i^(1/α)) · (y*)^((1-α)/α) + y* · (k · τ_max · e^(-k(y* - T*)))/(1 + e^(-k(y* - T*)))^2 · (1 + γ · σ²)
    
    The uncertainty term (1 + γ · σ²) accounts for behavioral frictions and optimization errors
    """
    y = y_optimal
    
    # Add firm-specific uncertainty
    np.random.seed(int(y) % 1000)  # Deterministic but varies by firm
    firm_uncertainty = np.random.normal(1.0, sigma_sq)  # Mean 1, variance σ²
    uncertainty_factor = 1 + gamma * firm_uncertainty
    
    # Left-hand side: net-of-tax rate
    exp_term = np.exp(-k * (y - T_star))
    exp_term = np.clip(exp_term, 1e-10, 1e10)  # Avoid overflow
    
    tau_y = tau_max / (1 + exp_term)
    lhs = 1 - tau_y
    
    # Right-hand side tax adjustment term with uncertainty
    rhs_tax_term = y * (k * tau_max * exp_term) / ((1 + exp_term) ** 2) * uncertainty_factor
    
    # Marginal cost coefficient that depends on A_i
    marginal_cost = lhs - rhs_tax_term / y  # Normalize by y
    
    if marginal_cost <= 0:
        return np.nan  # Invalid solution
    
    # Solve for A_i with uncertainty adjustment
    y_power = y ** ((1 - alpha) / alpha)
    coefficient = (1 / alpha) * y_power / marginal_cost
    
    if coefficient <= 0:
        return np.nan
    
    A_i = coefficient ** alpha
    
    return A_i


print("\n2. First, unbunch the observed distribution at £85k threshold...")

def unbunch_observed_distribution(current_turnover, current_threshold=85000, sigma=0.02):
    """
    Apply same bunching logic to unbunch £85k threshold as we use for £95k
    Use consistent methodology with distributional probabilities
    """
    np.random.seed(int(current_turnover) % 10000)
    
    # Distance from £85k threshold (firms below threshold)
    distance_from_threshold = current_threshold - current_turnover
    
    # Use economic breakeven distance as window (same logic as £95k model)
    vat_cost = 0.20
    breakeven_distance = current_threshold * vat_cost / (1 - vat_cost)  # £21,250
    
    if current_turnover <= current_threshold and distance_from_threshold < breakeven_distance:
        # Firms within economic breakeven distance - potential bunching
        # Much more conservative unbunching - most firms weren't actually bunching
        base_bunch_prob = 1 - (distance_from_threshold / breakeven_distance)
        
        # Reduce bunching assumption - only a fraction of eligible firms were actually bunching
        conservative_factor = 0.3  # Only 30% of theoretically eligible firms were bunching
        bunch_prob = base_bunch_prob * conservative_factor
        
        if np.random.random() < bunch_prob:
            # Conservative adjustment - smaller increases
            true_optimal_increase = np.random.exponential(scale=2000)  # Smaller than £95k scale
            true_optimal_increase = np.clip(true_optimal_increase, 500, 8000)  # More conservative range
            
            y_planned = current_threshold + true_optimal_increase
            
            # Apply uncertainty: y_realized = y_planned × (1 + ε)
            epsilon = np.random.normal(0, sigma)
            return y_planned * (1 + epsilon)
        else:
            # Not bunching, keep original - most firms
            return current_turnover
    else:
        # All other firms - no adjustment needed
        return current_turnover

# Apply unbunching to get corrected "true" turnover
print("   Estimating true FOC optimal turnover (unbunching £85k threshold)...")
df['true_turnover_unbunched'] = df['annual_turnover_k'].apply(
    lambda y: unbunch_observed_distribution(y * 1000)
)

print("\n3. Solving for corrected productivity (A_i) using unbunched distribution...")

# Apply reverse engineering to get implied productivity with uncertainty
gamma = 0.05  # Uncertainty parameter
sigma_sq = 0.02  # Variance parameter

print(f"   Using uncertainty parameters: γ={gamma}, σ²={sigma_sq}")
df['A_i_implied'] = (df['true_turnover_unbunched'] / 1000).apply(
    lambda y: solve_for_productivity(y * 1000, gamma=gamma, sigma_sq=sigma_sq)
)

# Remove invalid solutions
valid_mask = ~np.isnan(df['A_i_implied'])
df_valid = df[valid_mask].copy()
print(f"   ✓ Valid solutions for {len(df_valid):,} firms ({100*len(df_valid)/len(df):.1f}%)")

# Compare with actual productivity
if 'productivity' in df_valid.columns:
    print(f"\nComparison with actual productivity:")
    print(f"   Actual A_i - Mean: {df_valid['productivity'].mean():.6f}")
    print(f"   Implied A_i - Mean: {df_valid['A_i_implied'].mean():.6f}")
    print(f"   Correlation: {df_valid['productivity'].corr(df_valid['A_i_implied']):.3f}")

print("\n4. Calculating average A_i by turnover bands...")

# Define turnover bands
bands = [
    (0, 50000, "£0-50k"),
    (50000, 80000, "£50k-80k"),
    (80000, 85000, "£80k-85k (near threshold)"),
    (85000, 100000, "£85k-100k"),
    (100000, 150000, "£100k-150k"),
    (150000, 200000, "£150k-200k"),
    (200000, 300000, "£200k-300k"),
    (300000, 500000, "£300k-500k"),
    (500000, float('inf'), "£500k+")
]

print("\nAverage implied productivity (A_i) by turnover band:")
print("=" * 60)
print(f"{'Band':20} {'Count':8} {'Avg A_i':12} {'Std A_i':12} {'Avg Turnover':15}")
print("-" * 60)

band_results = []

for lower, upper, label in bands:
    mask = (df_valid['annual_turnover_k'] * 1000 >= lower) & (df_valid['annual_turnover_k'] * 1000 < upper)
    band_data = df_valid[mask]
    
    if len(band_data) > 0:
        count = len(band_data)
        avg_ai = np.average(band_data['A_i_implied'], weights=band_data['weight'])
        std_ai = np.sqrt(np.average((band_data['A_i_implied'] - avg_ai)**2, weights=band_data['weight']))
        avg_turnover = np.average(band_data['annual_turnover_k'] * 1000, weights=band_data['weight'])
        
        print(f"{label:20} {count:8,} {avg_ai:12.6f} {std_ai:12.6f} £{avg_turnover:13,.0f}")
        
        band_results.append({
            'band': label,
            'lower': lower,
            'upper': upper,
            'count': count,
            'avg_ai': avg_ai,
            'std_ai': std_ai,
            'avg_turnover': avg_turnover
        })
    else:
        print(f"{label:20} {0:8,} {'N/A':12} {'N/A':12} {'N/A':15}")

print("\n5. Analysis of productivity patterns...")

# Create DataFrame for analysis
results_df = pd.DataFrame(band_results)

if len(results_df) > 0:
    print(f"\nKey findings:")
    
    # Productivity trend
    print(f"   • Lowest productivity band: {results_df.loc[results_df['avg_ai'].idxmin(), 'band']} "
          f"(A_i = {results_df['avg_ai'].min():.6f})")
    print(f"   • Highest productivity band: {results_df.loc[results_df['avg_ai'].idxmax(), 'band']} "
          f"(A_i = {results_df['avg_ai'].max():.6f})")
    
    # Around threshold analysis
    near_threshold = results_df[results_df['band'] == "£80k-85k (near threshold)"]
    above_threshold = results_df[results_df['band'] == "£85k-100k"]
    
    if len(near_threshold) > 0 and len(above_threshold) > 0:
        print(f"   • Productivity just below threshold: {near_threshold['avg_ai'].iloc[0]:.6f}")
        print(f"   • Productivity just above threshold: {above_threshold['avg_ai'].iloc[0]:.6f}")
        productivity_jump = (above_threshold['avg_ai'].iloc[0] - near_threshold['avg_ai'].iloc[0]) / near_threshold['avg_ai'].iloc[0]
        print(f"   • Productivity jump at threshold: {productivity_jump:.1%}")

# Save results
results_df.to_csv('reverse_productivity_by_band.csv', index=False)
print(f"\n✓ Results saved to 'reverse_productivity_by_band.csv'")

print(f"\n" + "="*60)
print("INTERPRETATION")
print("="*60)
print("This analysis reverse-engineers productivity from actual turnover")
print("assuming firms are optimally responding to the current tax system.")
print("- Higher A_i in a band suggests firms need higher productivity to justify that turnover")
print("- Jumps in A_i around threshold suggest tax-induced selection effects")
print("- Compare with actual productivity to assess optimization realism")
print("\n✓ Reverse productivity estimation complete!")

# =============================================================================
# SECTION 5: APPLY NEW TAX FUNCTION (£95k threshold, 20% VAT)
# =============================================================================

print("\n" + "="*70)
print("APPLYING NEW TAX FUNCTION TO IMPLIED PRODUCTIVITY")
print("="*70)

# New tax parameters
T_star_new = 95000  # New threshold at £95k
tau_max_new = 0.20  # Same VAT rate
k_new = k  # Same sigmoid steepness

print(f"New tax system parameters:")
print(f"   T* (new threshold): £{T_star_new:,}")
print(f"   τ_max (VAT rate): {tau_max_new}")
print(f"   k (sigmoid steepness): {k_new}")

def solve_optimal_turnover_new_tax(A_i):
    """
    Given A_i (productivity), solve for optimal turnover under NEW tax function
    Pure FOC solution without any bunching
    """
    if np.isnan(A_i) or A_i <= 0:
        return np.nan
    
    # Better initial guess based on productivity
    y_no_tax = A_i * (alpha ** (alpha / (1 - alpha))) * 1000
    y = y_no_tax  # Start from no-tax optimal
    
    # Newton's method to solve FOC
    for _ in range(50):  # More iterations for convergence
        exp_term = np.exp(-k_new * (y - T_star_new))
        exp_term = np.clip(exp_term, 1e-10, 1e10)
        
        tau_y = tau_max_new / (1 + exp_term)
        tau_prime = (k_new * tau_max_new * exp_term) / ((1 + exp_term) ** 2)
        mc = (1/alpha) * (1/(A_i**(1/alpha))) * (y**((1-alpha)/alpha))
        
        residual = (1 - tau_y) - y * tau_prime - mc
        
        if abs(residual) < 1e-6:
            break
        
        # Fixed derivative calculation
        tau_double_prime = k_new * tau_prime * (1 - 2*tau_y/tau_max_new)
        dmc_dy = ((1-alpha)/alpha) * mc / y if y > 0 else 0
        dfoc_dy = -tau_prime - y * tau_double_prime - dmc_dy  # Fixed sign error
        
        if abs(dfoc_dy) > 1e-10:
            y_new = y - 0.5 * residual / dfoc_dy
            y = max(1000, min(1e7, y_new))
    
    return y

def apply_realistic_behavioral_adjustment(y_optimal, current_y, A_i):
    """
    Apply realistic behavioral adjustments to smooth the distribution
    """
    # 1. Add noise based on firm characteristics
    np.random.seed(int(current_y * A_i) % 10000)
    base_noise = np.random.normal(0, 3000)  # £3k standard deviation
    
    # 2. Size-dependent optimization capability
    if current_y < 30000:
        optimization_rate = 0.1  # Small firms barely optimize
    elif current_y < 75000:
        optimization_rate = 0.3  # Medium firms partially optimize
    elif current_y < 120000:
        optimization_rate = 0.5  # Larger firms optimize more
    else:
        optimization_rate = 0.7  # Large firms optimize well
    
    # 3. Limit maximum changes (realistic constraints)
    max_change = min(25000, abs(current_y * 0.4))  # Max 40% change or £25k
    optimal_change = y_optimal - current_y
    
    if abs(optimal_change) > max_change:
        direction = 1 if optimal_change > 0 else -1
        limited_change = direction * max_change
    else:
        limited_change = optimal_change
    
    # 4. Apply partial optimization with noise
    realistic_change = optimization_rate * limited_change + base_noise
    realistic_y = current_y + realistic_change
    
    # 5. Ensure reasonable bounds
    realistic_y = max(5000, min(500000, realistic_y))
    
    return realistic_y

print(f"\n6. Calculating optimal turnover under new tax function...")
print(f"   Solving FOC for {len(df_valid):,} firms with corrected productivity...")

# Step 1: Calculate pure optimal turnover (without bunching)
def solve_optimal_turnover_pure_foc(A_i):
    """Pure FOC solution without any bunching behavior"""
    if np.isnan(A_i) or A_i <= 0:
        return np.nan
    
    y = max(10000, min(200000, A_i * 50000))
    
    # Newton's method to solve FOC (no bunching modifications)
    for iteration in range(30):
        exp_term = np.exp(-k_new * (y - T_star_new))
        exp_term = np.clip(exp_term, 1e-10, 1e10)
        
        tau_y = tau_max_new / (1 + exp_term)
        tau_prime = (k_new * tau_max_new * exp_term) / ((1 + exp_term) ** 2)
        mc = (1/alpha) * (1/(A_i**(1/alpha))) * (y**((1-alpha)/alpha))
        
        residual = (1 - tau_y) - y * tau_prime - mc
        
        if abs(residual) < 1e-5:
            break
        
        tau_double_prime = k_new * tau_prime * (1 - 2*tau_y/tau_max_new)
        dmc_dy = ((1-alpha)/alpha) * mc / y if y > 0 else 0
        dfoc_dy = -tau_prime - y * tau_double_prime - dmc_dy
        
        if abs(dfoc_dy) > 1e-10:
            y_new = y - 0.3 * residual / dfoc_dy
            y = max(1000, min(1e7, y_new))
    
    return y  # Pure FOC solution - no bunching

df_valid['y_optimal_pure_foc'] = df_valid['A_i_implied'].apply(solve_optimal_turnover_pure_foc)
df_valid['y_optimal_pure'] = df_valid['A_i_implied'].apply(solve_optimal_turnover_new_tax)

# New: FOC + Uncertainty only (no bunching)
def add_uncertainty_only(y_optimal, current_y, new_threshold=95000, sigma=0.04):
    """
    Add only uncertainty term to FOC optimal - threshold-aware uncertainty
    Firms naturally avoid being close above thresholds due to uncertainty about future revenue
    This shows precautionary behavior through uncertainty term alone
    """
    np.random.seed(int(current_y) % 10000)
    
    # Distance above threshold
    distance_above = y_optimal - new_threshold
    
    if distance_above > 0 and distance_above < 10000:  # Close above threshold
        # Firms close above threshold face asymmetric risk:
        # - Small negative shock = stay below threshold (good)
        # - Small positive shock = pay VAT on all turnover (bad)
        # This creates natural incentive to have buffer below threshold
        
        # Asymmetric uncertainty: more likely to err downward when close above threshold
        # This is ONLY uncertainty - no bunching assumptions
        skewness = -1.5 * (1 - distance_above/10000)  # Stronger negative skew when closer to threshold
        epsilon = np.random.normal(skewness * sigma, sigma)
    else:
        # Standard symmetric uncertainty for all other firms
        epsilon = np.random.normal(0, sigma)
    
    return y_optimal * (1 + epsilon)

# Apply uncertainty-only model for £95k threshold
df_valid['y_uncertainty_only_95k'] = df_valid.apply(
    lambda row: add_uncertainty_only(row['y_optimal_pure_foc'], row['annual_turnover_k'] * 1000), 
    axis=1
)

# Apply uncertainty-only model for current distribution (£85k)
def add_uncertainty_only_current(current_y, current_threshold=85000, sigma=0.04):
    """Add threshold-aware uncertainty to current distribution around £85k"""
    np.random.seed(int(current_y) % 10000)
    
    # Distance above current threshold
    distance_above = current_y - current_threshold
    
    if distance_above > 0 and distance_above < 10000:  # Close above £85k threshold
        # Same asymmetric uncertainty logic for current threshold
        skewness = -1.5 * (1 - distance_above/10000)
        epsilon = np.random.normal(skewness * sigma, sigma)
    else:
        epsilon = np.random.normal(0, sigma)
    
    return current_y * (1 + epsilon)

df_valid['y_uncertainty_only_85k'] = df_valid.apply(
    lambda row: add_uncertainty_only_current(row['annual_turnover_k'] * 1000), 
    axis=1
)

# Skip realistic behavioral adjustments and simplified bunching - only need pure FOC and uncertainty

# Remove invalid solutions
valid_new_mask = ~np.isnan(df_valid['y_optimal_pure'])
df_new_valid = df_valid[valid_new_mask].copy()
print(f"   ✓ Valid solutions for {len(df_new_valid):,} firms ({100*len(df_new_valid)/len(df_valid):.1f}%)")

# =============================================================================
# SECTION 6: PLOT DISTRIBUTION COMPARISON
# =============================================================================

print(f"\n7. Creating distribution comparison plot...")

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

fig, ax = plt.subplots(1, 1, figsize=(12, 8))

# Focus on bunching regions £60k-120k to show both thresholds clearly
plot_range = (60000, 120000)
bins = np.linspace(plot_range[0], plot_range[1], 80)

# Filter data to plot range - use SAME firms for all distributions
# Base selection on original turnover to ensure consistency
mask_base = (df_new_valid['annual_turnover_k'] * 1000 >= plot_range[0] - 10000) & \
            (df_new_valid['annual_turnover_k'] * 1000 <= plot_range[1] + 10000)

# Use this consistent set of firms
df_plot = df_new_valid[mask_base]

# Calculate histograms - ensure same weights for all
# Use SAME firms and weights for fair comparison
common_weights = df_plot['weight'].values

hist_actual, edges = np.histogram(df_plot['annual_turnover_k'] * 1000, bins=bins, 
                                  weights=common_weights, density=False)
hist_pure_foc, _ = np.histogram(df_plot['y_optimal_pure_foc'], bins=bins,
                               weights=common_weights, density=False)
hist_uncertainty_only, _ = np.histogram(df_plot['y_uncertainty_only_95k'], bins=bins,
                                       weights=common_weights, density=False)

# Verify totals
print(f"   Histogram totals - Actual: {hist_actual.sum():.0f}, FOC: {hist_pure_foc.sum():.0f}, "
      f"Uncertainty Only: {hist_uncertainty_only.sum():.0f}")

bin_centers = (edges[:-1] + edges[1:]) / 2

# Create bunching version - move firms above threshold to just below
hist_bunched = hist_pure_foc.copy()
for i, center in enumerate(bin_centers):
    if center > T_star_new and center < T_star_new + 20000:  # Firms above threshold
        # Find bin just below threshold (around 93-94k)
        target_bin = np.argmin(np.abs(bin_centers - (T_star_new - 2000)))
        # Move 80% of these firms to bunching point
        hist_bunched[target_bin] += hist_bunched[i] * 0.8
        hist_bunched[i] *= 0.2

# Simple smoothing for ±20k around new threshold
from scipy.ndimage import gaussian_filter1d

# Smoothing window: ±20k around £95k threshold (£75k-£115k)
threshold_range = 35000  # £20k range around threshold
smooth_zone_mask = (bin_centers >= T_star_new - threshold_range) & (bin_centers <= T_star_new + threshold_range)
before_threshold_mask = smooth_zone_mask & (bin_centers <= T_star_new)
after_threshold_mask = smooth_zone_mask & (bin_centers > T_star_new)

# Create smooth curve only in ±20k zone
hist_smooth = hist_pure_foc.copy()  # Keep original outside smoothing zone

# Different smoothing for before/after threshold
smoothing_sigma_before = 5  # Heavy smoothing before (almost flat)
smoothing_sigma_after = 5    # Moderate smoothing after

# Apply different smoothing
hist_smooth[before_threshold_mask] = gaussian_filter1d(hist_pure_foc[before_threshold_mask], sigma=smoothing_sigma_before)
hist_smooth[after_threshold_mask] = gaussian_filter1d(hist_pure_foc[after_threshold_mask], sigma=smoothing_sigma_after)

# Plot distributions
ax.plot(bin_centers/1000, hist_actual, 'b-', linewidth=3, 
        label='Actual Distribution (Current Tax)', alpha=0.8)
ax.plot(bin_centers/1000, hist_pure_foc, 'red', linewidth=2, linestyle='-', 
        label='Pure FOC Optimal (New Tax)', alpha=0.5)
ax.plot(bin_centers/1000, hist_uncertainty_only, 'orange', linewidth=2, linestyle='-',
        label='FOC + Uncertainty Only (New Tax)', alpha=0.7)

# Add threshold lines
ax.axvline(x=85, color='gray', linestyle=':', linewidth=1.5, 
           alpha=0.5, label='Current Threshold (£85k)')
ax.axvline(x=95, color='black', linestyle='--', linewidth=2, 
           alpha=0.7, label='New Threshold (£95k)')

# Formatting
ax.set_xlabel('Turnover (£k)', fontsize=12)
ax.set_ylabel('Number of Firms', fontsize=12)
ax.set_title('Firm Distribution: Sigmoid vs Smoothed Tax Functions\n(Using Reverse-Engineered Productivity)', 
             fontsize=14, fontweight='bold')
ax.legend(fontsize=11, loc='upper right')
ax.grid(True, alpha=0.3)
ax.set_xlim([60, 120])
ax.set_xticks(range(60, 125, 5))  # Ticks every 5k from 60 to 120

# Summary statistics removed

plt.tight_layout()

# Save plot
output_file = 'reverse_productivity_new_tax_distribution.png'
try:
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"   ✓ Distribution plot saved to '{output_file}'")
except Exception as e:
    print(f"   ✗ Error saving plot: {e}")

plt.close()

# =============================================================================
# SECTION 7: ANALYSIS OF NEW TAX EFFECTS
# =============================================================================

print(f"\n8. Analyzing effects of new tax function...")

# Movement analysis for uncertainty only
df_new_valid['movement'] = df_new_valid['y_uncertainty_only_95k'] - (df_new_valid['annual_turnover_k'] * 1000)
df_new_valid['moved'] = abs(df_new_valid['movement']) > 1000  # More than £1k change

print(f"\nFirm Movement Analysis (Uncertainty Only):")
movers = df_new_valid['moved'].sum()
print(f"   Firms that would change turnover: {movers:,} ({100*movers/len(df_new_valid):.1f}%)")

if movers > 0:
    avg_movement = np.average(df_new_valid[df_new_valid['moved']]['movement'], 
                              weights=df_new_valid[df_new_valid['moved']]['weight'])
    print(f"   Average movement (movers only): £{avg_movement/1000:.1f}k")

# Threshold crossing analysis
current_above_85 = (df_new_valid['annual_turnover_k'] * 1000 > 85000).sum()
new_above_95 = (df_new_valid['y_uncertainty_only_95k'] > 95000).sum()
current_below_95 = (df_new_valid['annual_turnover_k'] * 1000 < 95000).sum()
new_below_95 = (df_new_valid['y_uncertainty_only_95k'] < 95000).sum()

print(f"\nThreshold Analysis:")
print(f"   Current: {current_above_85:,} firms above £85k ({100*current_above_85/len(df_new_valid):.1f}%)")
print(f"   New tax: {new_above_95:,} firms above £95k ({100*new_above_95/len(df_new_valid):.1f}%)")
print(f"   Firms that benefit from higher threshold: {current_below_95 - new_below_95:,}")

print(f"\n✓ New tax function analysis complete!")
print(f"\nKey Insight: This shows the THEORETICAL optimal distribution")
print(f"if all firms perfectly optimized under the new £95k threshold tax system.")