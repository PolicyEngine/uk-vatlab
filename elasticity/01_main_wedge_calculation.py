"""
VAT Effective Wedge Calculation - CORRECTED VERSION
Using UK 2022 Input-Output Tables with proper column interpretation

Formula: τ_e = λ(1-ρ)τ - τs_c·v
"""

import pandas as pd
import numpy as np

def get_uk_passthrough(sic_code):
    """UK-calibrated pass-through rates based on Crossley et al. (2009) and OBR (2011)"""
    
    sic_str = str(sic_code)
    sic_letter = sic_str[0] if sic_str else ''
    
    # UK-specific evidence
    if sic_letter == 'G':  # Retail/wholesale
        if 'G47' in sic_str:  # Retail
            return 0.90  # Very high pass-through
        else:  # G45, G46 wholesale
            return 0.85
    elif sic_letter == 'C':  # Manufacturing
        if any(x in sic_str for x in ['C101', 'C102', 'C103', 'C104', 'C105', 'C106', 'C107', 'C108']):
            return 0.80  # Food manufacturing - high pass-through
        else:
            return 0.85  # Other manufacturing
    elif sic_letter == 'I':  # Hospitality
        if 'I56' in sic_str:  # Food service
            return 0.35  # Low pass-through (menu costs)
        else:  # I55 accommodation
            return 0.40
    elif sic_letter == 'M':  # Professional services
        return 0.45  # Low-medium pass-through
    elif sic_letter == 'K':  # Financial
        return 0.40  # Low pass-through
    elif sic_letter == 'H':  # Transport
        return 0.70
    elif sic_letter == 'J':  # ICT
        return 0.65
    elif sic_letter == 'N':  # Administrative
        return 0.60
    elif sic_letter == 'Q':  # Health/social
        return 0.50
    elif sic_letter == 'R' or sic_letter == 'S':  # Arts/personal services
        return 0.45
    elif sic_letter in ['D', 'E']:  # Utilities
        return 0.90  # Regulated prices
    else:
        return 0.70  # Default medium

def get_vat_eligible_share(sic_code):
    """Estimate share of inputs eligible for VAT reclaim"""
    
    sic_str = str(sic_code)
    sic_letter = sic_str[0] if sic_str else ''
    
    # Financial services have lower VAT recovery
    if sic_letter == 'K':
        return 0.30  # Many financial services are VAT exempt
    elif sic_letter == 'Q':  # Health
        return 0.40  # NHS services are largely exempt
    elif sic_letter == 'P':  # Education
        return 0.35  # Education is VAT exempt
    elif sic_letter == 'L' and 'L68A' in sic_str:  # Owner-occupied housing
        return 0.0  # No VAT recovery
    else:
        return 0.95  # Most businesses can reclaim most input VAT

# Load the data
print("Loading UK 2022 Input-Output Tables...")
iot_df = pd.read_csv('iot_sheet.csv', skiprows=3)
a_df = pd.read_csv('a_sheet.csv', skiprows=3)

# Get industry codes and names
industry_codes = iot_df.iloc[:, 0].values[1:]  # Column 0 is SIC codes
industry_names = iot_df.iloc[:, 1].values[1:]  # Column 1 is names

# Find key columns
# Column 107 (_T): Total Intermediate Consumption
# Column 108 (P3 S1): Total Final Consumption
# Column 110 (P3 S14): Household Final Consumption (HFCE)
# Column 111 (P3 S15): NPISH
# Column 118 (TU): Total Use

print("\n=== CORRECTED CALCULATION ===")
print("λ = (HFCE + NPISH) / Total Output")
print("Total Output = Total Intermediate + Total Final Demand")
print("NOT using column 118 (TU) as it appears to be a different concept\n")

results = []

# For each industry (rows)
for i in range(105):  # 105 industries
    try:
        sic = industry_codes[i]
        name = industry_names[i]
        
        # Skip invalid rows
        if pd.isna(sic) or sic == '' or 'Total' in str(name):
            continue
            
        # Get s_c from A matrix (technical coefficients)
        # s_c = sum of column i (total intermediate inputs per unit output)
        column_data = a_df.iloc[1:106, i+2].apply(pd.to_numeric, errors='coerce')
        s_c = column_data.sum()
        
        # Get output data from IOT
        # Row i represents industry i's outputs to different uses
        row_data = iot_df.iloc[i+1, :]
        
        # Total intermediate consumption (sales to other industries)
        total_intermediate = pd.to_numeric(row_data.iloc[107], errors='coerce')
        
        # Final demand components
        total_final_consumption = pd.to_numeric(row_data.iloc[108], errors='coerce')
        gov_consumption = pd.to_numeric(row_data.iloc[109], errors='coerce')
        hfce = pd.to_numeric(row_data.iloc[110], errors='coerce')
        npish = pd.to_numeric(row_data.iloc[111], errors='coerce')
        gfcf = pd.to_numeric(row_data.iloc[112], errors='coerce')  # Investment
        exports_eu = pd.to_numeric(row_data.iloc[115], errors='coerce')
        exports_row = pd.to_numeric(row_data.iloc[116], errors='coerce')
        exports_services = pd.to_numeric(row_data.iloc[117], errors='coerce')
        
        # Calculate total output (sum of intermediate and final uses)
        total_output = (total_intermediate + total_final_consumption + 
                       gfcf + exports_eu + exports_row + exports_services)
        
        # Skip if no output
        if total_output <= 0 or pd.isna(total_output):
            continue
        
        # Calculate λ (B2C share) - CORRECTED
        b2c_sales = hfce + npish
        lambda_b2c = b2c_sales / total_output if total_output > 0 else 0
        
        # Get pass-through rate
        rho = get_uk_passthrough(sic)
        
        # Get VAT-eligible input share
        v = get_vat_eligible_share(sic)
        
        # Calculate effective wedge
        tau = 0.20  # UK VAT rate
        tau_e = lambda_b2c * (1 - rho) * tau - tau * s_c * v
        
        results.append({
            'SIC': sic,
            'Industry': name[:50],
            'λ (B2C share)': lambda_b2c,
            'ρ (pass-through)': rho,
            's_c (input share)': s_c,
            'v (VAT eligible)': v,
            'τ_e (wedge)': tau_e,
            'Total Output (£m)': total_output,
            'B2C Sales (£m)': b2c_sales
        })
        
    except Exception as e:
        continue

# Create DataFrame and analyze
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('τ_e (wedge)')

print("=== SUMMARY STATISTICS (CORRECTED) ===")
print(f"Total industries analyzed: {len(results_df)}")
print(f"\nλ (B2C share) statistics:")
print(f"  Mean: {results_df['λ (B2C share)'].mean():.3f}")
print(f"  Median: {results_df['λ (B2C share)'].median():.3f}")
print(f"  Min: {results_df['λ (B2C share)'].min():.3f}")
print(f"  Max: {results_df['λ (B2C share)'].max():.3f}")

print(f"\ns_c (input cost share) statistics:")
print(f"  Mean: {results_df['s_c (input share)'].mean():.3f}")
print(f"  Median: {results_df['s_c (input share)'].median():.3f}")
print(f"  Min: {results_df['s_c (input share)'].min():.3f}")
print(f"  Max: {results_df['s_c (input share)'].max():.3f}")

print(f"\nτ_e (effective wedge) distribution:")
negative_count = (results_df['τ_e (wedge)'] < 0).sum()
positive_count = (results_df['τ_e (wedge)'] >= 0).sum()
print(f"  Negative wedges: {negative_count} ({100*negative_count/len(results_df):.1f}%)")
print(f"  Positive wedges: {positive_count} ({100*positive_count/len(results_df):.1f}%)")
print(f"  Mean wedge: {results_df['τ_e (wedge)'].mean():.4f}")
print(f"  Median wedge: {results_df['τ_e (wedge)'].median():.4f}")

print("\n=== TOP 10 MOST NEGATIVE WEDGES (benefit most from VAT registration) ===")
print(results_df.head(10)[['SIC', 'Industry', 'λ (B2C share)', 'τ_e (wedge)']].to_string(index=False))

print("\n=== TOP 10 MOST POSITIVE WEDGES (benefit least/harmed by VAT) ===")
print(results_df.tail(10)[['SIC', 'Industry', 'λ (B2C share)', 'τ_e (wedge)']].to_string(index=False))

# Save results
results_df.to_csv('uk_wedge_calculations_corrected.csv', index=False)
print("\nResults saved to uk_wedge_calculations_corrected.csv")

# Check specific examples
print("\n=== SPECIFIC INDUSTRY EXAMPLES ===")
for sic_check in ['G47', 'C101', 'I56', 'M70', 'K64']:
    industry = results_df[results_df['SIC'] == sic_check]
    if not industry.empty:
        row = industry.iloc[0]
        print(f"\n{sic_check} - {row['Industry']}")
        print(f"  λ = {row['λ (B2C share)']:.3f} (B2C share of output)")
        print(f"  ρ = {row['ρ (pass-through)']:.2f}")
        print(f"  s_c = {row['s_c (input share)']:.3f}")
        print(f"  v = {row['v (VAT eligible)']:.2f}")
        print(f"  τ_e = {row['τ_e (wedge)']:.4f}")
        print(f"  Interpretation: {'Benefits from VAT registration' if row['τ_e (wedge)'] < 0 else 'Harmed by VAT'}")