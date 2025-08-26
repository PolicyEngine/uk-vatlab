#!/usr/bin/env python3
"""
Visualize the VAT threshold notch effect clearly.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set up the plot
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Tax liability discontinuity
ax = axes[0, 0]
turnover = np.linspace(70, 110, 1000)
vat_liability = np.where(turnover < 90, 0, turnover * 0.20 * 0.5)  # 20% VAT on 50% value-added

ax.plot(turnover, vat_liability, 'b-', linewidth=2)
ax.axvline(90, color='red', linestyle='--', alpha=0.5, label='VAT Threshold')
ax.fill_between([89, 91], 0, 10, alpha=0.3, color='red', label='Notch zone')
ax.set_xlabel('Annual Turnover (£k)')
ax.set_ylabel('VAT Liability (£k)')
ax.set_title('The VAT Notch: Discontinuous Tax Jump')
ax.grid(True, alpha=0.3)
ax.legend()

# Add annotation
ax.annotate('No VAT', xy=(85, 0.5), fontsize=12, color='green')
ax.annotate('20% VAT on ALL sales', xy=(95, 9), fontsize=12, color='red')
ax.annotate(f'Jump: £0 → £{90*0.2*0.5:.0f}k', 
            xy=(90, 5), xytext=(80, 7),
            arrowprops=dict(arrowstyle='->', color='red', lw=2),
            fontsize=11, color='red', fontweight='bold')

# 2. Effective tax rate
ax = axes[0, 1]
effective_rate = np.where(turnover < 90, 0, (turnover * 0.20 * 0.5) / turnover * 100)

ax.plot(turnover, effective_rate, 'g-', linewidth=2)
ax.axvline(90, color='red', linestyle='--', alpha=0.5, label='VAT Threshold')
ax.axhline(10, color='gray', linestyle=':', alpha=0.5)
ax.set_xlabel('Annual Turnover (£k)')
ax.set_ylabel('Effective Tax Rate (%)')
ax.set_title('Effective Tax Rate by Turnover')
ax.set_ylim(-1, 12)
ax.grid(True, alpha=0.3)
ax.legend()

# Add annotation
ax.annotate('Immediate 10% effective rate', 
            xy=(90, 10), xytext=(95, 8),
            arrowprops=dict(arrowstyle='->', color='green', lw=1.5),
            fontsize=10, color='green')

# 3. Firm distribution with bunching
ax = axes[1, 0]
np.random.seed(42)

# Generate turnover with bunching
base_turnover = np.random.lognormal(10.8, 0.8, 10000)
base_turnover = base_turnover[(base_turnover > 70) & (base_turnover < 110)]

# Add bunching effect
bunched_turnover = []
for t in base_turnover:
    if 88 < t < 92:
        if np.random.random() < 0.4:  # 40% bunch
            t = np.random.uniform(88, 89.9)
    elif 92 < t < 95:
        if np.random.random() < 0.2:  # Some avoid crossing
            t = np.random.uniform(88, 89.9)
    bunched_turnover.append(t)

# Plot both distributions
ax.hist(base_turnover, bins=40, alpha=0.5, color='blue', edgecolor='none', 
        label='Without VAT threshold', density=True)
ax.hist(bunched_turnover, bins=40, alpha=0.7, color='orange', edgecolor='black',
        label='With VAT threshold', density=True)
ax.axvline(90, color='red', linestyle='--', linewidth=2, label='Threshold')

# Highlight bunching zone
ax.axvspan(88, 90, alpha=0.2, color='yellow')
ax.text(89, ax.get_ylim()[1]*0.8, 'Bunching\nZone', ha='center', fontsize=10, 
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

ax.set_xlabel('Annual Turnover (£k)')
ax.set_ylabel('Density')
ax.set_title('Behavioral Response: Bunching Below Threshold')
ax.legend(loc='upper left')
ax.set_xlim(70, 110)

# 4. Revenue impact
ax = axes[1, 1]

thresholds = [85, 90, 95, 100]
revenues = [18.5, 17.2, 15.8, 14.5]  # Illustrative billions
distortion = [12, 8, 5, 3]  # Illustrative percentage

ax2 = ax.twinx()

bars = ax.bar(thresholds, revenues, width=3, alpha=0.7, color='steelblue', 
              edgecolor='black', label='VAT Revenue')
line = ax2.plot(thresholds, distortion, 'ro-', linewidth=2, markersize=8, 
                label='Economic Distortion')

ax.set_xlabel('VAT Threshold (£k)')
ax.set_ylabel('VAT Revenue (£ billions)', color='steelblue')
ax2.set_ylabel('Economic Distortion (%)', color='red')
ax.set_title('Revenue vs Distortion Trade-off')

# Add value labels
for bar, rev in zip(bars, revenues):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.2,
            f'£{height}B', ha='center', va='bottom', fontsize=9)

# Combine legends
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

ax.tick_params(axis='y', labelcolor='steelblue')
ax2.tick_params(axis='y', labelcolor='red')

plt.suptitle('Understanding the UK VAT Threshold Notch Effect', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('vat_notch_visualization.png', dpi=150, bbox_inches='tight')
# plt.show()  # Comment out to avoid hanging

print("\nKEY INSIGHTS FROM VISUALIZATION:")
print("="*50)
print("""
1. TOP LEFT: The VAT creates a sudden jump in tax liability at £90k
   - Below: £0 tax
   - At threshold: ~£9,000 tax (assuming 50% value-added)
   
2. TOP RIGHT: This creates a 10% effective tax rate immediately
   - Massive incentive to stay below threshold
   
3. BOTTOM LEFT: Firms respond by bunching below the threshold
   - Orange distribution shows concentration just below £90k
   - This is real economic activity being suppressed
   
4. BOTTOM RIGHT: Policy trade-off
   - Lower threshold = more revenue but more distortion
   - Higher threshold = less distortion but less revenue
   
The "notch" problem: It's not gradual - it's a cliff edge that distorts
business decisions and reduces economic efficiency.
""")