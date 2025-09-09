#!/usr/bin/env python3
"""
Generate a distribution bar chart of VAT-registered population by turnover band for 2023-24.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

# Read the data
df = pd.read_csv('data/HMRC_VAT_annual_statistics/vat_population_by_turnover_band.csv')

# Get 2023-24 data
data_2023_24 = df[df['Financial_Year'] == '2023-24'].iloc[0]

# Extract the turnover bands we want (including Negative_or_Zero)
bands = ['Negative_or_Zero', '£1_to_Threshold', '£Threshold_to_£150k', '£150k_to_£300k', 
         '£300k_to_£500k', '£500k_to_£1m', '£1m_to_£10m', 'Greater_than_£10m']

# Get the values for each band
values = [data_2023_24[band] for band in bands]

# Create cleaner labels for the x-axis
labels = ['≤£0', '£1-90k', '£90-150k', '£150-300k', '£300-500k', 
          '£500k-1m', '£1-10m', '>£10m']

# Create the bar chart
fig, ax = plt.subplots(figsize=(12, 7))

# Create bars with a nice color gradient
colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(bands)))
bars = ax.bar(labels, values, color=colors, edgecolor='darkblue', linewidth=1.5)

# Add value labels on top of each bar
for bar, value in zip(bars, values):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{value:,.0f}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

# Customize the plot
ax.set_xlabel('Turnover Band', fontsize=12, fontweight='bold')
ax.set_ylabel('Number of VAT-Registered Firms', fontsize=12, fontweight='bold')
ax.set_title('HMRC Distribution of VAT-Registered Firms by Turnover Band (2023-24)', 
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
plt.savefig('vat_population_distribution_2023_24.png', dpi=300, bbox_inches='tight')
print(f"Chart saved as 'vat_population_distribution_2023_24.png'")

# Also display the chart
plt.show()

# Print summary statistics
print("\nVAT-Registered Firms by Turnover Band (2023-24):")
print("-" * 50)
for label, value in zip(labels, values):
    percentage = (value / total) * 100
    print(f"{label:<15} {value:>10,} ({percentage:>5.1f}%)")
print("-" * 50)
print(f"{'Total':<15} {total:>10,} (100.0%)")

# Save data as JSON
json_data = {
    "title": "HMRC Distribution of VAT-Registered Firms by Turnover Band (2023-24)",
    "data_source": "HMRC VAT Annual Statistics",
    "financial_year": "2023-24",
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
    "additional_data": {
        "negative_or_zero": int(data_2023_24.get('Negative_or_Zero', 0)),
        "unknown": int(data_2023_24.get('Unknown', 0)),
        "grand_total": int(data_2023_24.get('Total', 0))
    }
}

# Save JSON file
with open('vat_population_distribution_2023_24.json', 'w') as f:
    json.dump(json_data, f, indent=2)
print(f"\nData saved as 'vat_population_distribution_2023_24.json'")