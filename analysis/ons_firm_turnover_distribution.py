#!/usr/bin/env python3
"""
Generate a distribution bar chart of firms by turnover band using ONS data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

# Read the ONS firm turnover data
df = pd.read_csv('data/ONS_UK_business_data/firm_turnover.csv')

# Define the turnover bands (in k)
bands = ['0-49', '50-99', '100-249', '250-499', '500-999', '1000-4999', '5000+']

# Sum all sectors (excluding SIC Code, Description, and Total columns)
total_by_band = df[bands].sum()

# Get the values for each band
values = total_by_band.values

# Create cleaner labels for the x-axis
labels = ['£0-49k', '£50-99k', '£100-249k', '£250-499k', 
          '£500-999k', '£1-5m', '£5m+']

# Create the bar chart
fig, ax = plt.subplots(figsize=(12, 7))

# Create bars with a nice color gradient
colors = plt.cm.Greens(np.linspace(0.4, 0.9, len(bands)))
bars = ax.bar(labels, values, color=colors, edgecolor='darkgreen', linewidth=1.5)

# Add value labels on top of each bar
for bar, value in zip(bars, values):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{value:,.0f}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

# Customize the plot
ax.set_xlabel('Turnover Band', fontsize=12, fontweight='bold')
ax.set_ylabel('Number of Firms', fontsize=12, fontweight='bold')
ax.set_title('Distribution of UK Firms by Turnover Band (ONS Data)', 
             fontsize=14, fontweight='bold', pad=20)

# Format y-axis with thousand separators
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

# Add grid for better readability
ax.grid(True, axis='y', alpha=0.3, linestyle='--')
ax.set_axisbelow(True)

# Rotate x-axis labels for better readability
plt.xticks(rotation=45, ha='right')

# Add total count as text
total = sum(values)
# ax.text(0.02, 0.98, f'Total firms: {total:,.0f}', 
#         transform=ax.transAxes, fontsize=11, 
#         verticalalignment='top',
#         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save the figure
plt.savefig('ons_firm_turnover_distribution.png', dpi=300, bbox_inches='tight')
print(f"Chart saved as 'ons_firm_turnover_distribution.png'")

# Also display the chart
plt.show()

# Print summary statistics
print("\nFirms by Turnover Band (ONS Data):")
print("-" * 50)
for label, value in zip(labels, values):
    percentage = (value / total) * 100
    print(f"{label:<15} {value:>10,.0f} ({percentage:>5.1f}%)")
print("-" * 50)
print(f"{'Total':<15} {total:>10,.0f} (100.0%)")

# Print sector breakdown for reference
print("\n\nTop 10 Sectors by Total Firms:")
print("-" * 50)
df_sorted = df.sort_values('Total', ascending=False).head(10)
for _, row in df_sorted.iterrows():
    print(f"{row['Description'][:50]:<50} {row['Total']:>10,.0f}")

# Save data as JSON
json_data = {
    "title": "Distribution of UK Firms by Turnover Band (ONS Data)",
    "data_source": "ONS UK Business Data",
    "turnover_bands": labels,
    "firm_counts": [int(v) for v in values],
    "percentages": [(float(v) / total) * 100 for v in values],
    "total_firms": int(total),
    "summary": {
        label: {
            "count": int(value),
            "percentage": round((value / total) * 100, 2)
        }
        for label, value in zip(labels, values)
    },
    "top_10_sectors": [
        {
            "sector": row['Description'],
            "sic_code": row['SIC Code'],
            "total_firms": int(row['Total'])
        }
        for _, row in df_sorted.iterrows()
    ]
}

# Save JSON file
with open('ons_firm_turnover_distribution.json', 'w') as f:
    json.dump(json_data, f, indent=2)
print(f"\nData saved as 'ons_firm_turnover_distribution.json'")