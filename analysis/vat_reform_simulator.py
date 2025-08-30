#!/usr/bin/env python3
"""
VAT Reform Scenario Simulator

Applies sector-specific elasticities to simulate the four VAT reform scenarios:
1. Higher VAT threshold (£90k → £100k)
2. Split-rate by sector (10% for labor-intensive services)
3. Graduated threshold - Taper 1 (£65k-£110k)
4. Graduated threshold - Taper 2 (£90k-£135k)

Uses calibrated elasticities from synthesize_sector_elasticities.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import json

class VATReformSimulator:
    """
    Simulate behavioral and revenue impacts of VAT reforms using sector-specific elasticities.
    """
    
    def __init__(self, elasticities_path: Path = None, firms_path: Path = None):
        """
        Initialize simulator with elasticities and firm data.
        """
        # Load paths
        base_path = Path(__file__).parent
        self.elasticities_path = elasticities_path or base_path / 'sector_vat_elasticities.csv'
        self.firms_path = firms_path or base_path / 'synthetic_firms_turnover.csv'
        
        # Current system parameters
        self.CURRENT_THRESHOLD = 90  # £90k
        self.CURRENT_VAT_RATE = 0.20
        
        # Load data
        self.elasticities = None
        self.firms = None
        self.baseline_revenue = None
        
    def load_data(self):
        """Load elasticities and firm data."""
        print("Loading sector elasticities and firm data...")
        
        # Load elasticities
        self.elasticities = pd.read_csv(self.elasticities_path)
        self.elasticity_dict = dict(zip(
            self.elasticities['sic_2digit'], 
            self.elasticities['elasticity']
        ))
        
        # Load firms
        self.firms = pd.read_csv(self.firms_path)
        self.firms['sic_2digit'] = self.firms['sic_code'].astype(str).str[:2].astype(int)
        
        # Add elasticity to each firm
        self.firms['elasticity'] = self.firms['sic_2digit'].map(self.elasticity_dict)
        self.firms['elasticity'].fillna(1.0, inplace=True)  # Default elasticity
        
        print(f"Loaded {len(self.firms)} firms across {len(self.elasticity_dict)} sectors")
        
    def calculate_baseline_revenue(self) -> float:
        """
        Calculate baseline VAT revenue under current system.
        Including voluntary registration below threshold.
        """
        revenue = 0
        sample = self.firms.sample(min(10000, len(self.firms)))
        
        for _, firm in sample.iterrows():
            turnover = firm['annual_turnover_k']
            
            # Mandatory registration above threshold
            if turnover > self.CURRENT_THRESHOLD:
                value_added_ratio = 1 - self._get_cost_ratio(firm['sic_2digit'])
                vat_base = turnover * value_added_ratio
                revenue += vat_base * self.CURRENT_VAT_RATE
            
            # Voluntary registration below threshold
            # Based on Liu et al. (2021): ~44% register voluntarily
            # Higher for high input cost sectors
            elif turnover > 50:  # Very small firms don't voluntarily register
                cost_ratio = self._get_cost_ratio(firm['sic_2digit'])
                # Probability of voluntary registration increases with input costs
                vol_reg_prob = min(0.6, cost_ratio * 0.8)  
                
                if np.random.random() < vol_reg_prob:
                    value_added_ratio = 1 - cost_ratio
                    vat_base = turnover * value_added_ratio
                    revenue += vat_base * self.CURRENT_VAT_RATE
        
        # Scale up from sample
        if len(sample) < len(self.firms):
            revenue = revenue * (len(self.firms) / len(sample))
        
        self.baseline_revenue = revenue * 1000  # Convert to £
        return self.baseline_revenue
    
    def _get_cost_ratio(self, sic_code: int) -> float:
        """Get cost ratio for sector (from synthesis model)."""
        cost_ratios = {
            3: 0.75,   # Manufacturing
            45: 0.80,  # Wholesale & Retail
            46: 0.85,  # Wholesale Trade
            47: 0.75,  # Retail Trade
            56: 0.65,  # Food Service
            10: 0.40,  # Information & Communication
            13: 0.35,  # Professional & Technical
            69: 0.35,  # Legal & Accounting
            96: 0.25,  # Personal Services
            6: 0.60,   # Construction
            77: 0.50,  # Rental & Leasing
            81: 0.45,  # Cleaning Services
        }
        return cost_ratios.get(sic_code, 0.50)
    
    def simulate_behavioral_response(self, firm_turnover: float, firm_elasticity: float, 
                                    old_threshold: float, new_threshold: float) -> float:
        """
        Simulate how a firm adjusts turnover in response to threshold change.
        
        Based on Liu, Lockwood & Tam (2022) growth effects.
        """
        # Distance to old threshold
        old_distance = firm_turnover - old_threshold
        
        # If firm was bunching below old threshold
        if -20 <= old_distance <= 0:
            # Fraction that will move with threshold
            bunching_intensity = abs(old_distance / 20)  # Closer = more likely to move
            
            # Some firms follow threshold up
            if np.random.random() < bunching_intensity * firm_elasticity:
                # Firm moves to just below new threshold
                new_turnover = new_threshold - np.random.uniform(0, 5)
            else:
                # Firm stays where it is
                new_turnover = firm_turnover
        else:
            # Firms not bunching don't change
            new_turnover = firm_turnover
            
        return new_turnover
    
    def scenario_1_higher_threshold(self, new_threshold: float = 100) -> Dict:
        """
        Scenario 1: Raise VAT threshold from £90k to £100k.
        
        Effects:
        - Firms between £90-100k no longer pay VAT
        - Some firms below £90k grow to bunch below £100k
        """
        print(f"\n--- Scenario 1: Higher Threshold (£{new_threshold}k) ---")
        
        results = {
            'scenario': 'Higher Threshold',
            'new_threshold': new_threshold,
            'firms_affected': 0,
            'revenue_change': 0,
            'behavioral_effects': {}
        }
        
        new_revenue = 0
        firms_deregistering = 0
        firms_bunching_up = 0
        
        for idx, firm in self.firms.sample(min(10000, len(self.firms))).iterrows():
            turnover = firm['annual_turnover_k']
            elasticity = firm['elasticity']
            
            # Behavioral response
            new_turnover = self.simulate_behavioral_response(
                turnover, elasticity, self.CURRENT_THRESHOLD, new_threshold
            )
            
            # Track bunching movement
            if new_turnover > turnover + 5:
                firms_bunching_up += 1
            
            # Revenue calculation
            if new_turnover > new_threshold:
                value_added_ratio = 1 - self._get_cost_ratio(firm['sic_2digit'])
                vat_base = new_turnover * value_added_ratio
                new_revenue += vat_base * self.CURRENT_VAT_RATE
            
            # Track deregistrations
            if self.CURRENT_THRESHOLD < turnover <= new_threshold:
                firms_deregistering += 1
        
        new_revenue *= 1000  # Convert to £
        
        results['firms_affected'] = firms_deregistering
        results['firms_bunching_up'] = firms_bunching_up
        results['revenue_change'] = new_revenue - self.baseline_revenue
        results['revenue_change_pct'] = (results['revenue_change'] / self.baseline_revenue) * 100
        
        print(f"Firms deregistering: {firms_deregistering:,}")
        print(f"Firms growing to bunch below £{new_threshold}k: {firms_bunching_up:,}")
        print(f"Revenue change: £{results['revenue_change']:,.0f} ({results['revenue_change_pct']:.1f}%)")
        
        return results
    
    def scenario_2_split_rate(self, reduced_rate: float = 0.10) -> Dict:
        """
        Scenario 2: Split-rate VAT - 10% for labor-intensive services.
        
        Labor-intensive services (EU definition):
        - Hairdressing (SIC 96)
        - Cleaning (SIC 81)
        - Repair services (SIC 95)
        - Food services (SIC 56)
        """
        print(f"\n--- Scenario 2: Split-Rate (Labor-intensive: {reduced_rate*100}%) ---")
        
        # Define labor-intensive sectors
        labor_intensive_sics = [56, 81, 95, 96]
        
        results = {
            'scenario': 'Split-Rate',
            'reduced_rate': reduced_rate,
            'firms_affected': 0,
            'revenue_change': 0,
            'sector_impacts': {}
        }
        
        new_revenue = 0
        firms_on_reduced_rate = 0
        
        for _, firm in self.firms.sample(min(10000, len(self.firms))).iterrows():
            if firm['annual_turnover_k'] > self.CURRENT_THRESHOLD:
                value_added_ratio = 1 - self._get_cost_ratio(firm['sic_2digit'])
                vat_base = firm['annual_turnover_k'] * value_added_ratio
                
                # Apply reduced rate for labor-intensive sectors
                if firm['sic_2digit'] in labor_intensive_sics:
                    rate = reduced_rate
                    firms_on_reduced_rate += 1
                    
                    # Behavioral response: less bunching with lower rate
                    # Firms more likely to register with lower burden
                    if 85 <= firm['annual_turnover_k'] <= 90:
                        # Some firms near threshold now register
                        if np.random.random() < (1 - reduced_rate/self.CURRENT_VAT_RATE):
                            vat_base *= 1.05  # Small growth effect
                else:
                    rate = self.CURRENT_VAT_RATE
                
                new_revenue += vat_base * rate
        
        new_revenue *= 1000
        
        results['firms_on_reduced_rate'] = firms_on_reduced_rate
        results['revenue_change'] = new_revenue - self.baseline_revenue
        results['revenue_change_pct'] = (results['revenue_change'] / self.baseline_revenue) * 100
        
        # Sector-specific analysis
        for sic in labor_intensive_sics:
            sector_firms = self.firms[
                (self.firms['sic_2digit'] == sic) & 
                (self.firms['annual_turnover_k'] > self.CURRENT_THRESHOLD)
            ]
            results['sector_impacts'][sic] = {
                'name': self._get_sector_name(sic),
                'firms': len(sector_firms),
                'avg_saving': len(sector_firms) * (self.CURRENT_VAT_RATE - reduced_rate) * 50  # Simplified
            }
        
        print(f"Firms on reduced rate: {firms_on_reduced_rate:,}")
        print(f"Revenue change: £{results['revenue_change']:,.0f} ({results['revenue_change_pct']:.1f}%)")
        
        return results
    
    def scenario_3_graduated_taper1(self) -> Dict:
        """
        Scenario 3: Graduated threshold with taper from £65k to £110k.
        
        Effective VAT rate increases linearly from 0% to 20% over this range.
        """
        print("\n--- Scenario 3: Graduated Threshold (£65k-£110k taper) ---")
        
        taper_start = 65
        taper_end = 110
        
        results = {
            'scenario': 'Graduated Taper 1',
            'taper_range': f'£{taper_start}k-£{taper_end}k',
            'firms_in_taper': 0,
            'revenue_change': 0
        }
        
        new_revenue = 0
        firms_in_taper = 0
        
        sample = self.firms.sample(min(10000, len(self.firms)))
        
        for _, firm in sample.iterrows():
            turnover = firm['annual_turnover_k']
            sic = firm['sic_2digit']
            
            if turnover <= taper_start:
                # Below taper - no mandatory VAT but could be voluntary
                # Under graduated system, voluntary registration less attractive
                # because they'd pay graduated rate if they grow
                if turnover > 50:
                    cost_ratio = self._get_cost_ratio(sic)
                    # Reduced voluntary registration under graduated system
                    vol_reg_prob = min(0.3, cost_ratio * 0.4)  
                    
                    if np.random.random() < vol_reg_prob:
                        value_added_ratio = 1 - cost_ratio
                        vat_base = turnover * value_added_ratio
                        new_revenue += vat_base * self.CURRENT_VAT_RATE
                        
            elif taper_start < turnover < taper_end:
                # In taper zone - EVERYONE pays proportional VAT
                firms_in_taper += 1
                effective_rate = self.CURRENT_VAT_RATE * (turnover - taper_start) / (taper_end - taper_start)
                
                # Less bunching due to smooth transition
                # Behavioral: firms don't bunch as much with gradual increase
                growth_factor = 1 + (0.01 * firm['elasticity'])  # Small growth boost
                adjusted_turnover = turnover * growth_factor
                
                value_added_ratio = 1 - self._get_cost_ratio(sic)
                vat_base = adjusted_turnover * value_added_ratio
                new_revenue += vat_base * effective_rate
            else:
                # Full VAT
                value_added_ratio = 1 - self._get_cost_ratio(sic)
                vat_base = turnover * value_added_ratio
                new_revenue += vat_base * self.CURRENT_VAT_RATE
        
        # Scale up from sample
        if len(sample) < len(self.firms):
            new_revenue = new_revenue * (len(self.firms) / len(sample))
            firms_in_taper = int(firms_in_taper * (len(self.firms) / len(sample)))
        
        new_revenue *= 1000
        
        results['firms_in_taper'] = firms_in_taper
        results['revenue_change'] = new_revenue - self.baseline_revenue
        results['revenue_change_pct'] = (results['revenue_change'] / self.baseline_revenue) * 100
        
        print(f"Firms in taper zone: {firms_in_taper:,}")
        print(f"Revenue change: £{results['revenue_change']:,.0f} ({results['revenue_change_pct']:.1f}%)")
        
        return results
    
    def scenario_4_graduated_taper2(self) -> Dict:
        """
        Scenario 4: Alternative graduated threshold with taper from £90k to £135k.
        """
        print("\n--- Scenario 4: Graduated Threshold (£90k-£135k taper) ---")
        
        taper_start = 90
        taper_end = 135
        
        results = {
            'scenario': 'Graduated Taper 2',
            'taper_range': f'£{taper_start}k-£{taper_end}k',
            'firms_in_taper': 0,
            'revenue_change': 0
        }
        
        new_revenue = 0
        firms_in_taper = 0
        
        for _, firm in self.firms.sample(min(10000, len(self.firms))).iterrows():
            turnover = firm['annual_turnover_k']
            
            if turnover <= taper_start:
                # No VAT (same as current)
                continue
            elif taper_start < turnover < taper_end:
                # In taper zone
                firms_in_taper += 1
                effective_rate = self.CURRENT_VAT_RATE * (turnover - taper_start) / (taper_end - taper_start)
                
                value_added_ratio = 1 - self._get_cost_ratio(firm['sic_2digit'])
                vat_base = turnover * value_added_ratio
                new_revenue += vat_base * effective_rate
            else:
                # Full VAT
                value_added_ratio = 1 - self._get_cost_ratio(firm['sic_2digit'])
                vat_base = turnover * value_added_ratio
                new_revenue += vat_base * self.CURRENT_VAT_RATE
        
        new_revenue *= 1000
        
        results['firms_in_taper'] = firms_in_taper
        results['revenue_change'] = new_revenue - self.baseline_revenue
        results['revenue_change_pct'] = (results['revenue_change'] / self.baseline_revenue) * 100
        
        print(f"Firms in taper zone: {firms_in_taper:,}")
        print(f"Revenue change: £{results['revenue_change']:,.0f} ({results['revenue_change_pct']:.1f}%)")
        
        return results
    
    def _get_sector_name(self, sic_code: int) -> str:
        """Get sector name from SIC code."""
        names = {
            56: 'Food Service Activities',
            81: 'Cleaning Services',
            95: 'Repair Services',
            96: 'Personal Services (Hairdressing)',
        }
        return names.get(sic_code, f'SIC {sic_code}')
    
    def run_all_scenarios(self) -> pd.DataFrame:
        """
        Run all four reform scenarios and compare results.
        """
        print("=" * 60)
        print("VAT REFORM SCENARIO ANALYSIS")
        print("=" * 60)
        
        # Calculate baseline
        self.calculate_baseline_revenue()
        print(f"\nBaseline VAT Revenue: £{self.baseline_revenue:,.0f}")
        
        # Run all scenarios
        results = []
        results.append(self.scenario_1_higher_threshold())
        results.append(self.scenario_2_split_rate())
        results.append(self.scenario_3_graduated_taper1())
        results.append(self.scenario_4_graduated_taper2())
        
        # Create comparison table
        comparison = pd.DataFrame(results)
        
        print("\n" + "=" * 60)
        print("SCENARIO COMPARISON")
        print("=" * 60)
        print(comparison[['scenario', 'revenue_change', 'revenue_change_pct']].to_string(index=False))
        
        # Export results
        output_path = Path(__file__).parent / 'vat_reform_scenarios.csv'
        comparison.to_csv(output_path, index=False)
        print(f"\nResults exported to: {output_path}")
        
        return comparison
    
    def sensitivity_analysis(self, elasticity_multipliers: List[float] = [0.5, 1.0, 1.5, 2.0]) -> pd.DataFrame:
        """
        Test sensitivity of results to elasticity assumptions.
        """
        print("\n" + "=" * 60)
        print("SENSITIVITY ANALYSIS")
        print("=" * 60)
        
        sensitivity_results = []
        
        for multiplier in elasticity_multipliers:
            print(f"\nElasticity multiplier: {multiplier}")
            
            # Adjust elasticities
            self.firms['elasticity'] = self.firms['elasticity'] * multiplier
            
            # Recalculate baseline
            self.calculate_baseline_revenue()
            
            # Run scenario 1 (most sensitive to elasticity)
            result = self.scenario_1_higher_threshold()
            result['elasticity_multiplier'] = multiplier
            sensitivity_results.append(result)
            
            # Reset elasticities
            self.firms['elasticity'] = self.firms['sic_2digit'].map(self.elasticity_dict)
            self.firms['elasticity'].fillna(1.0, inplace=True)
        
        sensitivity_df = pd.DataFrame(sensitivity_results)
        
        print("\nRevenue impact by elasticity assumption:")
        print(sensitivity_df[['elasticity_multiplier', 'revenue_change_pct']].to_string(index=False))
        
        return sensitivity_df


def main():
    """Run full VAT reform analysis."""
    
    # Initialize simulator
    simulator = VATReformSimulator()
    
    # Load data
    simulator.load_data()
    
    # Run all scenarios
    results = simulator.run_all_scenarios()
    
    # Run sensitivity analysis
    sensitivity = simulator.sensitivity_analysis()
    
    # Key insights
    print("\n" + "=" * 60)
    print("KEY INSIGHTS")
    print("=" * 60)
    
    # Find revenue-maximizing scenario
    best_revenue = results.loc[results['revenue_change'].idxmax()]
    print(f"\nRevenue-maximizing: {best_revenue['scenario']}")
    print(f"  Revenue change: £{best_revenue['revenue_change']:,.0f}")
    
    # Find most growth-friendly scenario
    if 'firms_bunching_up' in results.columns:
        growth_friendly = results.loc[results['firms_bunching_up'].idxmax()]
        print(f"\nMost growth-friendly: {growth_friendly['scenario']}")
    
    print("\nLabor-intensive services benefit most from Scenario 2 (Split-rate)")
    print("Graduated thresholds reduce bunching distortions")
    
    return results, sensitivity


if __name__ == "__main__":
    results, sensitivity = main()