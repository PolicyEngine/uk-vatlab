#!/usr/bin/env python3
"""
Quick synthetic firm generation for VAT threshold analysis.
Generates a simplified dataset quickly for testing.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def generate_quick_synthetic_firms(n_firms=100000):
    """Generate synthetic firms with turnover distribution matching UK patterns."""
    
    np.random.seed(42)
    
    # Create turnover distribution with bunching at £85k threshold
    # Based on literature: ~1% growth slowdown near threshold
    
    # Generate base turnover (log-normal distribution)
    base_turnover = np.random.lognormal(mean=10.5, sigma=1.8, size=n_firms)
    
    # Add bunching effect near £85k (old threshold) and £90k (new threshold)
    turnover = []
    for t in base_turnover:
        if 80000 < t < 85000:
            # 20% probability to bunch just below £85k
            if np.random.random() < 0.20:
                t = np.random.uniform(83000, 84999)
        elif 85000 < t < 90000:
            # 15% probability to bunch just below £90k
            if np.random.random() < 0.15:
                t = np.random.uniform(88000, 89999)
        elif 90000 < t < 95000:
            # Reduced density just above threshold (firms avoiding growth)
            if np.random.random() < 0.3:
                t = np.random.uniform(88000, 89999)
        
        turnover.append(t)
    
    turnover = np.array(turnover)
    
    # Generate sectors (simplified)
    sectors = np.random.choice(
        ['Retail', 'Manufacturing', 'Services', 'Construction', 'Technology'],
        size=n_firms,
        p=[0.25, 0.15, 0.35, 0.15, 0.10]
    )
    
    # Generate employment (correlated with turnover)
    employment = np.maximum(1, (turnover / 50000) + np.random.normal(0, 2, n_firms))
    employment = np.round(employment).astype(int)
    
    # Create DataFrame
    df = pd.DataFrame({
        'firm_id': range(n_firms),
        'annual_turnover': turnover,
        'annual_turnover_k': turnover / 1000,  # In thousands
        'sector': sectors,
        'employment': employment,
        'vat_registered': turnover > 90000  # Simple registration rule
    })
    
    # Save to CSV
    output_path = Path(__file__).parent / 'synthetic_firms_quick.csv'
    df.to_csv(output_path, index=False)
    
    print(f"Generated {n_firms:,} synthetic firms")
    print(f"Saved to: {output_path}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"  Firms below £85k: {(df['annual_turnover'] < 85000).sum():,}")
    print(f"  Firms £85k-£90k: {((df['annual_turnover'] >= 85000) & (df['annual_turnover'] < 90000)).sum():,}")
    print(f"  Firms above £90k: {(df['annual_turnover'] >= 90000).sum():,}")
    print(f"  VAT registered: {df['vat_registered'].sum():,}")
    
    return df

if __name__ == "__main__":
    df = generate_quick_synthetic_firms()