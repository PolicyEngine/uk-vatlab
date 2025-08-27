#!/usr/bin/env python3
"""
VAT threshold bunching analysis by sector.
Calculates ratio of firms just below to just above £90k threshold.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_vat_threshold_bunching():
    """Analyze bunching behavior around VAT threshold by sector."""
    
    # Load synthetic data
    data_path = Path(__file__).parent / 'synthetic_firms_turnover.csv'
    df = pd.read_csv(data_path)
    
    # Convert SIC code to numeric sector (first digit)
    df['sector'] = df['sic_code'].astype(str).str[:2].astype(int)
    
    # Define threshold windows
    # Just below: £85k-90k (5k window below threshold)
    # Just above: £90k-95k (5k window above threshold)
    below_min, below_max = 85, 90
    above_min, above_max = 90, 95
    
    # Sector names mapping
    sector_names = {
        1: 'Agriculture, Forestry & Fishing',
        2: 'Mining & Quarrying', 
        3: 'Manufacturing',
        5: 'Water Supply & Waste',
        6: 'Construction',
        8: 'Transportation & Storage',
        9: 'Accommodation & Food Service',
        10: 'Information & Communication',
        11: 'Financial & Insurance',
        13: 'Professional & Technical',
        14: 'Administrative & Support',
        15: 'Public Admin & Defence',
        16: 'Education',
        17: 'Health & Social Work',
        18: 'Arts & Entertainment',
        19: 'Other Service Activities',
        20: 'Activities of Households',
        21: 'Extraterritorial Organizations',
        22: 'Real Estate Activities',
        23: 'Scientific Research',
        24: 'Advertising & Market Research',
        25: 'Other Professional Activities',
        26: 'Veterinary Activities',
        27: 'Travel Agency',
        28: 'Security & Investigation',
        29: 'Services to Buildings',
        30: 'Office Admin & Support',
        31: 'Creative, Arts & Entertainment',
        32: 'Libraries & Archives',
        33: 'Sports & Recreation',
        35: 'Electricity & Gas Supply',
        36: 'Water Collection & Treatment',
        37: 'Sewerage',
        38: 'Waste Collection & Treatment',
        39: 'Remediation Activities',
        41: 'Construction of Buildings',
        42: 'Civil Engineering',
        43: 'Specialized Construction',
        45: 'Wholesale & Retail Trade',
        46: 'Wholesale Trade',
        47: 'Retail Trade',
        49: 'Land Transport',
        50: 'Water Transport',
        51: 'Air Transport',
        52: 'Warehousing & Support',
        53: 'Postal & Courier',
        55: 'Accommodation',
        56: 'Food & Beverage Service',
        58: 'Publishing Activities',
        59: 'Motion Picture & TV',
        60: 'Programming & Broadcasting',
        61: 'Telecommunications',
        62: 'Computer Programming',
        63: 'Information Service',
        64: 'Financial Service',
        65: 'Insurance & Reinsurance',
        66: 'Activities Auxiliary to Finance',
        68: 'Real Estate Activities',
        69: 'Legal & Accounting',
        70: 'Head Offices & Management',
        71: 'Architecture & Engineering',
        72: 'Scientific Research & Development',
        73: 'Advertising & Market Research',
        74: 'Other Professional Activities',
        75: 'Veterinary Activities',
        77: 'Rental & Leasing',
        78: 'Employment Activities',
        79: 'Travel Agency & Tour',
        80: 'Security & Investigation',
        81: 'Services to Buildings',
        82: 'Office Admin & Support',
        84: 'Public Admin & Defence',
        85: 'Education',
        86: 'Human Health',
        87: 'Residential Care',
        88: 'Social Work',
        90: 'Creative, Arts & Entertainment',
        91: 'Libraries & Archives',
        92: 'Gambling & Betting',
        93: 'Sports & Recreation',
        94: 'Activities of Membership Orgs',
        95: 'Repair of Computers',
        96: 'Other Personal Service',
        97: 'Activities of Households as Employers',
        98: 'Undifferentiated Goods Production',
        99: 'Activities of Extraterritorial Orgs'
    }
    
    # Calculate bunching metrics by sector
    results = []
    
    for sector in sorted(df['sector'].unique()):
        sector_df = df[df['sector'] == sector]
        
        # Count weighted firms in each window
        firms_below = sector_df[
            (sector_df['annual_turnover_k'] > below_min) & 
            (sector_df['annual_turnover_k'] <= below_max)
        ]['weight'].sum()
        
        firms_above = sector_df[
            (sector_df['annual_turnover_k'] > above_min) & 
            (sector_df['annual_turnover_k'] <= above_max)
        ]['weight'].sum()
        
        # Skip if either is zero (can't calculate meaningful ratio)
        if firms_below == 0 or firms_above == 0:
            continue
            
        # Calculate ratio
        ratio = firms_below / firms_above
        
        # Get sector name
        sector_name = sector_names.get(sector, f'Sector {sector}')
        
        # Total firms in sector
        total_firms = sector_df['weight'].sum()
        
        # Percentage of firms near threshold (80-100k range)
        firms_near_threshold = sector_df[
            (sector_df['annual_turnover_k'] > 80) & 
            (sector_df['annual_turnover_k'] <= 100)
        ]['weight'].sum()
        pct_near_threshold = (firms_near_threshold / total_firms * 100) if total_firms > 0 else 0
        
        results.append({
            'sector_code': sector,
            'sector_name': sector_name,
            'firms_below_threshold': firms_below,
            'firms_above_threshold': firms_above,
            'bunching_ratio': ratio,
            'total_firms': total_firms,
            'pct_near_threshold': pct_near_threshold
        })
    
    # Convert to DataFrame and sort by bunching ratio
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('bunching_ratio', ascending=False)
    
    # Save full results
    output_path = Path(__file__).parent / 'vat_threshold_bunching_by_sector_no_zeros.csv'
    results_df.to_csv(output_path, index=False)
    
    # Print TOP 20
    print("\n" + "="*100)
    print("VAT THRESHOLD BUNCHING ANALYSIS BY SECTOR (EXCLUDING ZERO VALUES)")
    print("Ratio of firms just below (£85-90k) to just above (£90-95k) threshold")
    print("="*100)
    print("\nTOP 20 SECTORS (HIGHEST BUNCHING):")
    print(f"{'Rank':<5} {'Sector':<45} {'Ratio':<10} {'Below':<10} {'Above':<10} {'% Near':<8}")
    print(f"{'':5} {'':45} {'':10} {'(85-90k)':<10} {'(90-95k)':<10} {'Threshold':<8}")
    print("-"*100)
    
    for idx, row in enumerate(results_df.head(20).itertuples(), 1):
        # Format sector name to fit
        sector_name = row.sector_name[:43] if len(row.sector_name) > 43 else row.sector_name
        
        print(f"{idx:<5} {sector_name:<45} {row.bunching_ratio:>8.2f}x  "
              f"{row.firms_below_threshold:>9,.0f}  {row.firms_above_threshold:>9,.0f}  "
              f"{row.pct_near_threshold:>7.1f}%")
    
    # Print BOTTOM 20
    print("\n" + "="*100)
    print("BOTTOM 20 SECTORS (LOWEST BUNCHING):")
    print(f"{'Rank':<5} {'Sector':<45} {'Ratio':<10} {'Below':<10} {'Above':<10} {'% Near':<8}")
    print(f"{'':5} {'':45} {'':10} {'(85-90k)':<10} {'(90-95k)':<10} {'Threshold':<8}")
    print("-"*100)
    
    bottom_20 = results_df.tail(20).sort_values('bunching_ratio', ascending=True)
    for idx, row in enumerate(bottom_20.itertuples(), 1):
        # Format sector name to fit
        sector_name = row.sector_name[:43] if len(row.sector_name) > 43 else row.sector_name
        
        print(f"{idx:<5} {sector_name:<45} {row.bunching_ratio:>8.2f}x  "
              f"{row.firms_below_threshold:>9,.0f}  {row.firms_above_threshold:>9,.0f}  "
              f"{row.pct_near_threshold:>7.1f}%")
    
    print("-"*100)
    
    # Summary statistics
    print("\nSUMMARY STATISTICS:")
    print(f"  Total sectors analyzed (with data in both ranges): {len(results_df)}")
    print(f"  Average bunching ratio across sectors: {results_df['bunching_ratio'].mean():.2f}x")
    print(f"  Median bunching ratio: {results_df['bunching_ratio'].median():.2f}x")
    print(f"  Highest ratio: {results_df['bunching_ratio'].max():.2f}x ({results_df.iloc[0]['sector_name']})")
    print(f"  Lowest ratio: {results_df['bunching_ratio'].min():.2f}x ({results_df.iloc[-1]['sector_name']})")
    
    # Sectors with strong bunching (ratio > 2)
    strong_bunching = results_df[results_df['bunching_ratio'] > 2]
    print(f"\n  Sectors with strong bunching (ratio > 2x): {len(strong_bunching)}")
    
    # Sectors with reverse bunching (ratio < 1)
    reverse_bunching = results_df[results_df['bunching_ratio'] < 1]
    print(f"  Sectors with reverse bunching (ratio < 1x): {len(reverse_bunching)}")
    
    return results_df

if __name__ == "__main__":
    results = analyze_vat_threshold_bunching()