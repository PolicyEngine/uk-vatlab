#!/usr/bin/env python3
"""
VAT Threshold Analysis with Synthetic UK Firms

Demonstrates the effects of VAT threshold changes using elasticities from the literature:
- Liu et al. (2019): Turnover elasticity 0.09-0.18
- IMF (2024): 1pp growth slowdown near threshold
- Bunching behavior: 15-20% of firms near threshold
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.vat_simulation import VATSimulator, VATPolicy

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def load_synthetic_firms():
    """Load synthetic firm data."""
    data_path = Path(__file__).parent / 'synthetic_firms_quick.csv'
    if not data_path.exists():
        print("Generating synthetic data...")
        from generate_synthetic_quick import generate_quick_synthetic_firms
        return generate_quick_synthetic_firms()
    return pd.read_csv(data_path)


def plot_turnover_distribution(firms, policies_results, save_path=None):
    """Plot turnover distribution showing bunching effects."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Original distribution
    ax = axes[0, 0]
    ax.hist(firms['annual_turnover'] / 1000, bins=100, alpha=0.7, color='blue', edgecolor='black')
    ax.axvline(90, color='red', linestyle='--', label='Current threshold (£90k)')
    ax.set_xlabel('Annual Turnover (£k)')
    ax.set_ylabel('Number of Firms')
    ax.set_title('Original Turnover Distribution')
    ax.set_xlim(0, 200)
    ax.legend()
    
    # Distribution after behavioral response
    ax = axes[0, 1]
    adjusted_firms = policies_results['Current']['adjusted_firms']
    ax.hist(adjusted_firms['annual_turnover'] / 1000, bins=100, alpha=0.7, color='green', edgecolor='black')
    ax.axvline(90, color='red', linestyle='--', label='Threshold')
    ax.set_xlabel('Annual Turnover (£k)')
    ax.set_ylabel('Number of Firms')
    ax.set_title('After Behavioral Response (Bunching)')
    ax.set_xlim(0, 200)
    ax.legend()
    
    # Zoom in on threshold region
    ax = axes[1, 0]
    threshold_region = adjusted_firms[
        (adjusted_firms['annual_turnover'] >= 70000) & 
        (adjusted_firms['annual_turnover'] <= 110000)
    ]
    ax.hist(threshold_region['annual_turnover'] / 1000, bins=40, alpha=0.7, color='orange', edgecolor='black')
    ax.axvline(90, color='red', linestyle='--', linewidth=2, label='VAT Threshold')
    ax.axvspan(85, 90, alpha=0.2, color='yellow', label='Bunching zone')
    ax.set_xlabel('Annual Turnover (£k)')
    ax.set_ylabel('Number of Firms')
    ax.set_title('Bunching Near Threshold (Zoomed)')
    ax.legend()
    
    # Revenue comparison
    ax = axes[1, 1]
    policies = list(policies_results.keys())
    revenues = [policies_results[p]['vat_revenue'] / 1e9 for p in policies]
    behavioral_costs = [-policies_results[p]['behavioral_adjustment'] / 1e9 for p in policies]
    
    x = np.arange(len(policies))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, revenues, width, label='Total Revenue', color='steelblue')
    bars2 = ax.bar(x + width/2, behavioral_costs, width, label='Behavioral Cost', color='coral')
    
    ax.set_xlabel('Policy Scenario')
    ax.set_ylabel('Revenue (£ billions)')
    ax.set_title('VAT Revenue Impact by Policy')
    ax.set_xticks(x)
    ax.set_xticklabels(policies, rotation=45, ha='right')
    ax.legend()
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'£{height:.1f}B', ha='center', va='bottom')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def create_policy_comparison_table(policies_results):
    """Create a comparison table of different VAT policies."""
    rows = []
    for name, result in policies_results.items():
        policy = result['policy']
        rows.append({
            'Policy': name,
            'Threshold': f"£{policy.threshold:,.0f}",
            'Standard Rate': f"{policy.standard_rate:.1%}",
            'Revenue (£B)': f"{result['vat_revenue'] / 1e9:.2f}",
            'Registered Firms': f"{result['num_registered']:,}",
            'Bunching Firms': f"{result['firms_bunching']:,}",
            'Behavioral Cost (£M)': f"{-result['behavioral_adjustment'] / 1e6:.1f}",
            'Effective Revenue Loss': f"{-result['behavioral_adjustment'] / result['baseline_revenue']:.1%}"
        })
    
    df = pd.DataFrame(rows)
    return df


def run_sensitivity_analysis(firms):
    """Run sensitivity analysis on elasticity parameters."""
    elasticities = [0.09, 0.12, 0.14, 0.16, 0.18]  # Range from Liu et al.
    bunching_rates = [0.10, 0.15, 0.20, 0.25]  # Range of bunching behaviors
    
    results = []
    
    for elasticity in elasticities:
        for bunching in bunching_rates:
            sim = VATSimulator(firms, 
                             elasticity_turnover=elasticity,
                             bunching_rate=bunching)
            policy = VATPolicy(threshold=90000)
            result = sim.simulate(policy)
            
            results.append({
                'Elasticity': elasticity,
                'Bunching Rate': bunching,
                'Revenue (£B)': result['vat_revenue'] / 1e9,
                'Behavioral Cost (£M)': -result['behavioral_adjustment'] / 1e6,
                'Firms Bunching': result['firms_bunching']
            })
    
    sensitivity_df = pd.DataFrame(results)
    
    # Create heatmap
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Revenue heatmap
    pivot_revenue = sensitivity_df.pivot(index='Bunching Rate', 
                                         columns='Elasticity', 
                                         values='Revenue (£B)')
    sns.heatmap(pivot_revenue, annot=True, fmt='.2f', cmap='YlOrRd', ax=axes[0])
    axes[0].set_title('VAT Revenue Sensitivity (£ Billions)')
    
    # Behavioral cost heatmap
    pivot_cost = sensitivity_df.pivot(index='Bunching Rate', 
                                      columns='Elasticity', 
                                      values='Behavioral Cost (£M)')
    sns.heatmap(pivot_cost, annot=True, fmt='.1f', cmap='RdYlBu_r', ax=axes[1])
    axes[1].set_title('Behavioral Cost Sensitivity (£ Millions)')
    
    plt.tight_layout()
    plt.savefig('vat_sensitivity_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    return sensitivity_df


def main():
    """Run main VAT threshold analysis."""
    print("=" * 60)
    print("VAT THRESHOLD SIMULATION ANALYSIS")
    print("Based on empirical elasticities from UK literature")
    print("=" * 60)
    
    # Load synthetic firms
    print("\n1. Loading synthetic firm data...")
    firms = load_synthetic_firms()
    print(f"   Loaded {len(firms):,} firms")
    print(f"   Firms below £85k: {(firms['annual_turnover'] < 85000).sum():,}")
    print(f"   Firms £85k-£90k: {((firms['annual_turnover'] >= 85000) & (firms['annual_turnover'] < 90000)).sum():,}")
    print(f"   Firms above £90k: {(firms['annual_turnover'] >= 90000).sum():,}")
    
    # Initialize simulator with literature-based parameters
    print("\n2. Initializing VAT simulator...")
    print("   Elasticity: 0.14 (mid-point from Liu et al. 2019)")
    print("   Bunching rate: 15% (observed in UK data)")
    print("   Growth slowdown: 1pp (IMF 2024)")
    sim = VATSimulator(firms)
    
    # Define policy scenarios
    print("\n3. Defining policy scenarios...")
    policies = {
        'Current': VATPolicy(threshold=90000, standard_rate=0.20),
        'Lower Threshold': VATPolicy(threshold=85000, standard_rate=0.20),
        'Higher Threshold': VATPolicy(threshold=100000, standard_rate=0.20),
        'Reduced Rates': VATPolicy(
            threshold=90000,
            standard_rate=0.20,
            reduced_rates={
                (30000, 60000): 0.10,  # 10% for £30k-£60k
                (60000, 90000): 0.15   # 15% for £60k-£90k
            }
        ),
        'Lower Rate': VATPolicy(threshold=90000, standard_rate=0.175),
    }
    
    # Run simulations
    print("\n4. Running simulations...")
    results = {}
    for name, policy in policies.items():
        print(f"   Simulating: {name}...")
        results[name] = sim.simulate(policy)
    
    # Create comparison table
    print("\n5. Policy Comparison Results:")
    print("-" * 60)
    comparison_df = create_policy_comparison_table(results)
    print(comparison_df.to_string(index=False))
    
    # Save results
    comparison_df.to_csv('vat_policy_comparison.csv', index=False)
    print("\n   Results saved to: vat_policy_comparison.csv")
    
    # Create visualizations
    print("\n6. Creating visualizations...")
    plot_turnover_distribution(firms, results, 'vat_threshold_analysis.png')
    print("   Saved: vat_threshold_analysis.png")
    
    # Run sensitivity analysis
    print("\n7. Running sensitivity analysis...")
    sensitivity_df = run_sensitivity_analysis(firms)
    print("   Saved: vat_sensitivity_analysis.png")
    
    # Key insights
    print("\n" + "=" * 60)
    print("KEY INSIGHTS FROM SIMULATION")
    print("=" * 60)
    
    current = results['Current']
    lower = results['Lower Threshold']
    reduced = results['Reduced Rates']
    
    print(f"""
1. BUNCHING EFFECT:
   - {current['firms_bunching']:,} firms bunch just below £90k threshold
   - This represents {current['firms_bunching']/len(firms)*100:.1f}% of all firms
   
2. REVENUE IMPACT OF THRESHOLD CHANGE:
   - Lowering threshold to £85k: +£{(lower['vat_revenue'] - current['vat_revenue'])/1e9:.2f}B revenue
   - But increases distortions: {lower['firms_bunching']:,} firms bunching
   
3. BEHAVIORAL COSTS:
   - Current policy loses £{-current['behavioral_adjustment']/1e6:.1f}M to behavioral responses
   - This is {-current['behavioral_adjustment']/current['baseline_revenue']*100:.1f}% of potential revenue
   
4. MARGINAL RATES OPTION:
   - Reduced rates for small firms changes revenue by £{(reduced['vat_revenue'] - current['vat_revenue'])/1e9:.2f}B
   - Could reduce distortions while maintaining coverage
    """)
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()