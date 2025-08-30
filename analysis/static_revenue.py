"""
Static Revenue Analysis for VAT Threshold Bunching
Calculates VAT liability for each firm based on sector-level data and weights
"""

import pandas as pd
import numpy as np
import os

# Get the current directory (analysis folder)
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)

# Load the data
print("Loading data...")
synthetic_firms = pd.read_csv(os.path.join(current_dir, 'synthetic_firms_turnover.csv'))
vat_liability_by_sector = pd.read_csv(os.path.join(base_dir, 'data/HMRC_VAT_annual_statistics/vat_liability_by_sector.csv'))

# Convert VAT liability from £ millions to £
vat_liability_by_sector['vat_liability_pounds'] = vat_liability_by_sector['2023-24'] * 1_000_000

# Create a mapping from sic_code to VAT liability
sic_to_vat = dict(zip(vat_liability_by_sector['Trade_Sector'], 
                      vat_liability_by_sector['vat_liability_pounds']))

weighted_total_firms = synthetic_firms['weight'].sum()
print(f"Loaded {weighted_total_firms:,.0f} firms and {len(vat_liability_by_sector)} sectors")

# Step 1: Calculate weighted sector totals
print("\nCalculating weighted sector totals...")
weighted_sector_totals = synthetic_firms.groupby('sic_code').apply(
    lambda x: (x['annual_turnover_k'] * x['weight']).sum()
)

# Step 2: Calculate each firm's share using weights
def calculate_firm_vat(row):
    sector = row['sic_code']
    
    # Check if sector exists in VAT liability data
    if sector not in sic_to_vat:
        return 0
    
    # Firm's weighted turnover (in thousands)
    firm_weighted_turnover = row['annual_turnover_k'] * row['weight']
    
    # Sector's total weighted turnover
    sector_weighted_total = weighted_sector_totals.get(sector, 0)
    
    if sector_weighted_total == 0:
        return 0
    
    # Firm's share of sector
    firm_share = firm_weighted_turnover / sector_weighted_total
    
    # Firm's VAT liability (already population-weighted)
    sector_vat_liability = sic_to_vat[sector]
    firm_vat_liability = firm_share * sector_vat_liability
    
    return firm_vat_liability

print("Calculating VAT liability for each firm...")
synthetic_firms['vat_liability'] = synthetic_firms.apply(calculate_firm_vat, axis=1)

# Save the updated dataframe with VAT liability
print("\nSaving updated data with VAT liability...")
synthetic_firms.to_csv(os.path.join(current_dir, 'synthetic_firms_turnover.csv'), index=False)

# Step 3: Static revenue impact analysis
# Convert turnover from thousands to pounds for threshold comparison
synthetic_firms['annual_turnover'] = synthetic_firms['annual_turnover_k'] * 1000

# Identify firms in the bunching region (£90k to £100k)
affected = synthetic_firms[
    (synthetic_firms['annual_turnover'] >= 90000) & 
    (synthetic_firms['annual_turnover'] < 100000)
]

# Calculate total revenue loss (no need to multiply by weight again!)
total_revenue_loss = affected['vat_liability'].sum()
total_revenue_loss_millions = total_revenue_loss / 1_000_000

# Summary statistics (applying weights)
total_weighted_firms = synthetic_firms['weight'].sum()
affected_weighted_firms = affected['weight'].sum()

print("\n" + "="*60)
print("STATIC REVENUE IMPACT ANALYSIS")
print("="*60)
print(f"Total firms in dataset: {total_weighted_firms:,.0f}")
print(f"Firms in bunching region (£90k-£100k): {affected_weighted_firms:,.0f}")
print(f"Percentage of firms affected: {affected_weighted_firms/total_weighted_firms*100:.2f}%")
print(f"\nTotal VAT liability in bunching region: £{total_revenue_loss_millions:,.2f} million")
print(f"Average VAT per affected firm: £{total_revenue_loss/affected_weighted_firms:,.2f}" if affected_weighted_firms > 0 else "N/A")

# Additional analysis by sector
print("\n" + "="*60)
print("TOP 5 SECTORS BY VAT LIABILITY IN BUNCHING REGION")
print("="*60)
if len(affected) > 0:
    sector_impact = affected.groupby('sic_code').agg({
        'vat_liability': 'sum',
        'weight': 'sum'
    }).rename(columns={'weight': 'weighted_firm_count'})
    sector_impact = sector_impact.sort_values('vat_liability', ascending=False).head(5)
    
    for idx, (sector, row) in enumerate(sector_impact.iterrows(), 1):
        sector_name = vat_liability_by_sector[
            vat_liability_by_sector['Trade_Sector'] == sector
        ]['Trade_Sub_Sector'].values
        sector_name = sector_name[0] if len(sector_name) > 0 else "Unknown"
        vat_millions = row['vat_liability'] / 1_000_000
        print(f"{idx}. {sector} - {sector_name[:50]}")
        print(f"   Firms: {row['weighted_firm_count']:,.0f}, VAT: £{vat_millions:.2f} million")

# Check data quality
print("\n" + "="*60)
print("DATA QUALITY CHECKS")
print("="*60)
print(f"Firms with missing SIC codes: {synthetic_firms[synthetic_firms['sic_code'].isna()]['weight'].sum():,.0f}")
print(f"Firms with zero/negative turnover: {synthetic_firms[synthetic_firms['annual_turnover_k'] <= 0]['weight'].sum():,.0f}")
print(f"Raw records with zero/negative weights: {(synthetic_firms['weight'] <= 0).sum()}")
print(f"Firms with calculated VAT liability: {synthetic_firms[synthetic_firms['vat_liability'] != 0]['weight'].sum():,.0f}")
total_vat_billions = synthetic_firms['vat_liability'].sum() / 1_000_000_000
print(f"Total VAT liability across all firms: £{total_vat_billions:,.2f} billion")