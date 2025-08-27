"""
Create summary visualization of VAT wedge analysis results
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data
df = pd.read_csv('uk_wedge_calculations_corrected.csv')

# Create figure with multiple subplots
fig = plt.figure(figsize=(14, 10))

# 1. Distribution of Effective Wedges
ax1 = plt.subplot(2, 3, 1)
ax1.hist(df['τ_e (wedge)'], bins=30, color='steelblue', edgecolor='black', alpha=0.7)
ax1.axvline(x=0, color='red', linestyle='--', label='Zero wedge')
ax1.set_xlabel('Effective Wedge (τ_e)')
ax1.set_ylabel('Number of Industries')
ax1.set_title('Distribution of VAT Effective Wedges')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. B2C Share Distribution
ax2 = plt.subplot(2, 3, 2)
ax2.hist(df['λ (B2C share)'], bins=30, color='green', edgecolor='black', alpha=0.7)
ax2.set_xlabel('B2C Share (λ)')
ax2.set_ylabel('Number of Industries')
ax2.set_title('Distribution of B2C Sales Share')
ax2.grid(True, alpha=0.3)

# 3. Wedge vs B2C Share
ax3 = plt.subplot(2, 3, 3)
colors = ['red' if x >= 0 else 'blue' for x in df['τ_e (wedge)']]
ax3.scatter(df['λ (B2C share)'], df['τ_e (wedge)'], alpha=0.6, c=colors)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax3.set_xlabel('B2C Share (λ)')
ax3.set_ylabel('Effective Wedge (τ_e)')
ax3.set_title('Wedge vs B2C Share')
ax3.grid(True, alpha=0.3)

# 4. Top industries by wedge
ax4 = plt.subplot(2, 3, 4)
top_negative = df.nsmallest(10, 'τ_e (wedge)')
industries_short = [name[:25] + '...' if len(name) > 25 else name 
                   for name in top_negative['Industry']]
ax4.barh(range(len(industries_short)), top_negative['τ_e (wedge)'].values, color='darkblue')
ax4.set_yticks(range(len(industries_short)))
ax4.set_yticklabels(industries_short, fontsize=8)
ax4.set_xlabel('Effective Wedge')
ax4.set_title('Top 10 Industries Benefiting from VAT Registration')
ax4.grid(True, alpha=0.3, axis='x')

# 5. Industries harmed by VAT
ax5 = plt.subplot(2, 3, 5)
positive_wedge = df[df['τ_e (wedge)'] > 0].nlargest(10, 'τ_e (wedge)')
if len(positive_wedge) > 0:
    industries_pos = [name[:25] + '...' if len(name) > 25 else name 
                     for name in positive_wedge['Industry']]
    ax5.barh(range(len(industries_pos)), positive_wedge['τ_e (wedge)'].values, color='darkred')
    ax5.set_yticks(range(len(industries_pos)))
    ax5.set_yticklabels(industries_pos, fontsize=8)
ax5.set_xlabel('Effective Wedge')
ax5.set_title('Industries Harmed by VAT Registration')
ax5.grid(True, alpha=0.3, axis='x')

# 6. Summary statistics box
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')
summary_text = f"""
KEY STATISTICS

Wedge Distribution:
• Negative (benefit): {(df['τ_e (wedge)'] < 0).sum()} industries ({100*(df['τ_e (wedge)'] < 0).mean():.1f}%)
• Positive (harmed): {(df['τ_e (wedge)'] >= 0).sum()} industries ({100*(df['τ_e (wedge)'] >= 0).mean():.1f}%)
• Mean wedge: {df['τ_e (wedge)'].mean():.4f}
• Median wedge: {df['τ_e (wedge)'].median():.4f}

B2C Share (λ):
• Mean: {df['λ (B2C share)'].mean():.3f}
• Median: {df['λ (B2C share)'].median():.3f}

Input Costs (s_c):
• Mean: {df['s_c (input share)'].mean():.3f}
• Median: {df['s_c (input share)'].median():.3f}

THE PUZZLE:
90% of industries benefit from VAT
registration, yet firms bunch below
the threshold. This suggests compliance
costs (~£3-5k/year) are crucial.
"""
ax6.text(0.1, 0.9, summary_text, fontsize=10, verticalalignment='top', fontfamily='monospace')

plt.suptitle('UK VAT Effective Wedge Analysis - Summary Results', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('vat_wedge_summary_visualization.png', dpi=150, bbox_inches='tight')
plt.show()

print("Summary visualization saved as 'vat_wedge_summary_visualization.png'")