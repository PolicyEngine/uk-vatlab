#!/usr/bin/env python3
"""
Synthesize Sector-Specific VAT Elasticities from UK Bunching Data

This module estimates sector-specific elasticities of turnover with respect to 
VAT thresholds by combining:
1. Observed bunching ratios from UK synthetic firm data
2. Literature-based priors from empirical studies
3. Sector characteristics (B2C share, input costs, labor intensity)

Key References:
- Liu, Lockwood & Tam (2022): "Small Firm Growth and the VAT Threshold" 
  Overall UK elasticity ≈ 1.0 percentage point growth slowdown
- Kleven & Waseem (2013): Bunching formula relating excess mass to elasticity
- Harju et al. (2019): Finnish hairdressing VAT reduction (22% to 8%)
- Bellon et al. (2024): Heterogeneous VAT pass-through rates

Author: UK VATLab Analysis Team
Date: 2024
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import optimize
from typing import Dict, Tuple, Optional
import warnings

class SectorElasticityCalibrator:
    """
    Calibrate sector-specific VAT elasticities using observed bunching behavior
    and literature-based priors.
    """
    
    def __init__(self, data_path: Path = None):
        """
        Initialize calibrator with data paths and literature parameters.
        
        Parameters:
        -----------
        data_path : Path
            Path to synthetic_firms_turnover.csv
        """
        self.data_path = data_path or Path(__file__).parent / 'synthetic_firms_turnover.csv'
        
        # Literature-based parameters (Liu, Lockwood & Tam 2022)
        self.BASE_ELASTICITY = 1.0  # Baseline growth slowdown in percentage points
        self.VAT_RATE = 0.20  # UK standard VAT rate
        self.THRESHOLD = 90  # VAT threshold in £1000s
        
        # Window for bunching analysis (£1000s)
        self.BUNCHING_WINDOW_BELOW = 5  # £85k-90k
        self.BUNCHING_WINDOW_ABOVE = 5  # £90k-95k
        
        # Initialize storage
        self.sector_data = None
        self.elasticities = {}
        
    def load_and_prepare_data(self) -> pd.DataFrame:
        """
        Load synthetic firm data and calculate bunching metrics by sector.
        
        Returns:
        --------
        pd.DataFrame with columns:
            - sic_2digit: 2-digit SIC code
            - sector_name: Sector description
            - bunching_ratio: Ratio of firms below/above threshold
            - firms_below: Count in £85-90k range
            - firms_above: Count in £90-95k range
            - avg_turnover: Average turnover in sector
            - avg_cost_ratio: Average cost/turnover ratio
        """
        print("Loading synthetic firm data...")
        df = pd.read_csv(self.data_path)
        
        # Extract 2-digit SIC code
        df['sic_2digit'] = df['sic_code'].astype(str).str[:2].astype(int)
        
        # Calculate bunching metrics by sector
        sector_metrics = []
        
        for sic in df['sic_2digit'].unique():
            sector_df = df[df['sic_2digit'] == sic]
            
            # Count firms in bunching windows
            firms_below = len(sector_df[
                (sector_df['annual_turnover_k'] >= 85) & 
                (sector_df['annual_turnover_k'] < 90)
            ])
            
            firms_above = len(sector_df[
                (sector_df['annual_turnover_k'] >= 90) & 
                (sector_df['annual_turnover_k'] < 95)
            ])
            
            # Calculate bunching ratio (avoid division by zero)
            if firms_above > 0:
                bunching_ratio = firms_below / firms_above
            else:
                bunching_ratio = firms_below / 1  # Use 1 to avoid infinity
            
            # Calculate sector characteristics
            avg_turnover = sector_df['annual_turnover_k'].mean()
            # Estimate cost ratio based on sector type (since cost data not in this file)
            avg_cost_ratio = self._estimate_cost_ratio(sic)
            
            sector_metrics.append({
                'sic_2digit': sic,
                'sector_name': self._get_sector_name(sic),
                'bunching_ratio': bunching_ratio,
                'firms_below': firms_below,
                'firms_above': firms_above,
                'total_firms': len(sector_df),
                'avg_turnover': avg_turnover,
                'avg_cost_ratio': avg_cost_ratio
            })
        
        self.sector_data = pd.DataFrame(sector_metrics)
        return self.sector_data
    
    def _get_sector_name(self, sic_code: int) -> str:
        """
        Map 2-digit SIC code to sector name.
        
        Source: UK SIC 2007 classification
        """
        sic_names = {
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
            41: 'Construction',
            45: 'Wholesale & Retail Trade',
            46: 'Wholesale Trade',
            47: 'Retail Trade',
            49: 'Land Transport',
            55: 'Accommodation',
            56: 'Food Service Activities',
            62: 'Computer Programming',
            68: 'Real Estate Activities',
            69: 'Legal & Accounting',
            70: 'Management Consultancy',
            71: 'Architecture & Engineering',
            73: 'Advertising & Market Research',
            77: 'Rental & Leasing',
            81: 'Services to Buildings',
            86: 'Human Health',
            87: 'Residential Care',
            88: 'Social Work',
            90: 'Creative Arts',
            93: 'Sports & Recreation',
            95: 'Repair of Computers & Household Goods',
            96: 'Other Personal Services'
        }
        return sic_names.get(sic_code, f'SIC {sic_code}')
    
    def _estimate_cost_ratio(self, sic_code: int) -> float:
        """
        Estimate cost/turnover ratio based on sector characteristics.
        
        Based on industry knowledge and typical margins.
        """
        # High cost ratio sectors (low margins)
        high_cost = {
            3: 0.75,   # Manufacturing
            45: 0.80,  # Wholesale & Retail Trade
            46: 0.85,  # Wholesale Trade
            47: 0.75,  # Retail Trade
            56: 0.65,  # Food Service
        }
        
        # Low cost ratio sectors (high margins, service-based)
        low_cost = {
            10: 0.40,  # Information & Communication
            13: 0.35,  # Professional & Technical
            62: 0.30,  # Computer Programming
            69: 0.35,  # Legal & Accounting
            70: 0.30,  # Management Consultancy
            96: 0.25,  # Personal Services (hairdressing - labor costs not materials)
        }
        
        # Medium cost ratio sectors
        medium_cost = {
            6: 0.60,   # Construction
            9: 0.55,   # Accommodation & Food
            77: 0.50,  # Rental & Leasing
            81: 0.45,  # Cleaning Services
            95: 0.50,  # Repair Services
        }
        
        if sic_code in high_cost:
            return high_cost[sic_code]
        elif sic_code in low_cost:
            return low_cost[sic_code]
        elif sic_code in medium_cost:
            return medium_cost[sic_code]
        else:
            return 0.50  # Default middle value
    
    def get_literature_prior(self, sic_code: int) -> Dict[str, float]:
        """
        Get literature-based elasticity priors for a sector.
        
        Based on:
        - Liu, Lockwood & Tam (2022): UK overall elasticity
        - Harju et al. (2019): Finnish service sector elasticities
        - Literature findings on B2C vs B2B differences
        
        Returns:
        --------
        Dict with 'elasticity' and 'confidence' (0-1)
        """
        
        # Labor-intensive services (based on EU definitions)
        labor_intensive_services = {
            9: 1.5,   # Accommodation & Food: High B2C, labor intensive
            18: 1.3,  # Arts & Entertainment: High B2C
            19: 1.6,  # Other Services (includes hairdressing): Very high B2C
            56: 1.5,  # Food Service: High B2C, labor intensive
            81: 1.4,  # Cleaning Services: Labor intensive
            93: 1.3,  # Sports & Recreation: B2C dominant
            95: 1.4,  # Repair Services: EU labor-intensive category
            96: 1.6   # Personal Services (hairdressing): Highest elasticity
        }
        
        # Manufacturing and construction (high input costs)
        high_input_sectors = {
            3: 0.6,   # Manufacturing: High inputs, mostly B2B
            6: 0.7,   # Construction: High materials cost
            41: 0.7,  # Construction of buildings
            45: 0.8,  # Wholesale & Retail Trade
            46: 0.7,  # Wholesale Trade: Pure B2B
        }
        
        # Professional services (mostly B2B)
        professional_services = {
            10: 0.8,  # Information & Communication
            11: 0.7,  # Financial & Insurance: Mostly exempt
            13: 0.9,  # Professional & Technical
            62: 0.8,  # Computer Programming: B2B
            69: 0.9,  # Legal & Accounting
            70: 0.9,  # Management Consultancy
            71: 0.8,  # Architecture & Engineering
        }
        
        # Check which category the sector falls into
        if sic_code in labor_intensive_services:
            return {
                'elasticity': labor_intensive_services[sic_code],
                'confidence': 0.8,
                'source': 'Labor-intensive services prior'
            }
        elif sic_code in high_input_sectors:
            return {
                'elasticity': high_input_sectors[sic_code],
                'confidence': 0.7,
                'source': 'High input cost sectors prior'
            }
        elif sic_code in professional_services:
            return {
                'elasticity': professional_services[sic_code],
                'confidence': 0.7,
                'source': 'Professional B2B services prior'
            }
        else:
            # Default prior
            return {
                'elasticity': self.BASE_ELASTICITY,
                'confidence': 0.5,
                'source': 'Default UK average (Liu et al. 2022)'
            }
    
    def calibrate_elasticity_from_bunching(
        self, 
        bunching_ratio: float, 
        prior: Dict[str, float],
        cost_ratio: float
    ) -> float:
        """
        Calibrate elasticity using observed bunching and prior.
        
        Based on Kleven & Waseem (2013) bunching formula:
        B = e * t / (1 + e * t)
        
        Where:
        - B is excess bunching mass
        - e is elasticity
        - t is tax rate change at threshold
        
        Adjusted for UK context with voluntary registration.
        
        Parameters:
        -----------
        bunching_ratio : float
            Observed ratio of firms below/above threshold
        prior : dict
            Literature-based prior elasticity and confidence
        cost_ratio : float
            Average cost/turnover ratio for sector
        
        Returns:
        --------
        float : Calibrated elasticity
        """
        
        # Adjust bunching ratio for voluntary registration
        # High input cost sectors have more voluntary registration (Liu et al. 2021)
        voluntary_adjustment = 1 - (cost_ratio * 0.3)  # Higher costs = less bunching
        adjusted_bunching = bunching_ratio * voluntary_adjustment
        
        # Convert bunching ratio to excess mass
        # Bunching ratio of 2.0 means 100% excess mass
        excess_mass = max(0, adjusted_bunching - 1.0)
        
        # Effective tax wedge at threshold
        # For non-registered: pay embedded VAT on inputs
        # For registered: charge VAT on outputs but reclaim on inputs
        effective_tax_wedge = self.VAT_RATE * (1 - cost_ratio)
        
        # Initial elasticity from bunching formula
        if effective_tax_wedge > 0:
            # Solve B = e * t / (1 + e * t) for e
            if excess_mass > 0:
                elasticity_observed = excess_mass / (effective_tax_wedge * (1 - excess_mass))
            else:
                elasticity_observed = 0
        else:
            elasticity_observed = prior['elasticity']
        
        # Bayesian combination with prior
        prior_weight = prior['confidence']
        observed_weight = min(0.8, excess_mass)  # Higher bunching = more reliable
        
        combined_elasticity = (
            prior['elasticity'] * prior_weight + 
            elasticity_observed * observed_weight
        ) / (prior_weight + observed_weight)
        
        # Apply reasonable bounds
        return np.clip(combined_elasticity, 0.1, 3.0)
    
    def estimate_b2c_share(self, sic_code: int) -> float:
        """
        Estimate B2C share for sector based on industry characteristics.
        
        Based on Liu et al. (2021) and industry knowledge.
        """
        high_b2c_sectors = {
            9: 0.9,   # Accommodation & Food
            47: 0.95, # Retail Trade
            55: 0.9,  # Accommodation
            56: 0.95, # Food Service
            77: 0.7,  # Rental & Leasing
            93: 0.9,  # Sports & Recreation
            95: 0.8,  # Repair Services
            96: 0.95  # Personal Services (hairdressing)
        }
        
        low_b2c_sectors = {
            3: 0.2,   # Manufacturing
            10: 0.3,  # Information & Communication
            46: 0.1,  # Wholesale Trade
            62: 0.2,  # Computer Programming
            69: 0.2,  # Legal & Accounting
            70: 0.15, # Management Consultancy
            71: 0.2   # Architecture & Engineering
        }
        
        if sic_code in high_b2c_sectors:
            return high_b2c_sectors[sic_code]
        elif sic_code in low_b2c_sectors:
            return low_b2c_sectors[sic_code]
        else:
            return 0.5  # Default middle value
    
    def calibrate_all_sectors(self) -> pd.DataFrame:
        """
        Calibrate elasticities for all sectors.
        
        Returns:
        --------
        DataFrame with calibrated elasticities and metadata
        """
        if self.sector_data is None:
            self.load_and_prepare_data()
        
        results = []
        
        for _, sector in self.sector_data.iterrows():
            sic = sector['sic_2digit']
            
            # Get literature prior
            prior = self.get_literature_prior(sic)
            
            # Calibrate elasticity
            elasticity = self.calibrate_elasticity_from_bunching(
                bunching_ratio=sector['bunching_ratio'],
                prior=prior,
                cost_ratio=sector['avg_cost_ratio']
            )
            
            # Estimate B2C share
            b2c_share = self.estimate_b2c_share(sic)
            
            results.append({
                'sic_2digit': sic,
                'sector_name': sector['sector_name'],
                'elasticity': round(elasticity, 3),
                'bunching_ratio': round(sector['bunching_ratio'], 2),
                'firms_in_sector': sector['total_firms'],
                'avg_cost_ratio': round(sector['avg_cost_ratio'], 3),
                'b2c_share_estimate': b2c_share,
                'prior_elasticity': prior['elasticity'],
                'calibration_source': prior['source'],
                'confidence': self._calculate_confidence(sector)
            })
        
        self.results = pd.DataFrame(results)
        return self.results
    
    def _calculate_confidence(self, sector_row) -> str:
        """
        Calculate confidence level based on data quality.
        """
        if sector_row['firms_below'] + sector_row['firms_above'] > 100:
            return 'High'
        elif sector_row['firms_below'] + sector_row['firms_above'] > 30:
            return 'Medium'
        else:
            return 'Low'
    
    def identify_labor_intensive_services(self) -> pd.DataFrame:
        """
        Identify labor-intensive services per EU definition.
        
        These are candidates for reduced VAT rates under split-rate scenario.
        """
        labor_intensive_sics = [
            9,   # Accommodation & Food Service
            56,  # Food Service Activities  
            81,  # Services to Buildings (cleaning)
            95,  # Repair Services
            96   # Other Personal Services (hairdressing)
        ]
        
        if self.results is None:
            self.calibrate_all_sectors()
        
        labor_intensive = self.results[
            self.results['sic_2digit'].isin(labor_intensive_sics)
        ].copy()
        
        labor_intensive['eu_labor_intensive'] = True
        labor_intensive['proposed_vat_rate'] = 10  # Reduced rate
        
        return labor_intensive
    
    def validate_elasticities(self) -> Dict[str, float]:
        """
        Validate calibrated elasticities against known benchmarks.
        
        Returns:
        --------
        Dictionary of validation metrics
        """
        if self.results is None:
            self.calibrate_all_sectors()
        
        # Weight elasticities by firm count
        weighted_avg = np.average(
            self.results['elasticity'],
            weights=self.results['firms_in_sector']
        )
        
        # Compare to Liu, Lockwood & Tam (2022) benchmark
        benchmark_diff = abs(weighted_avg - self.BASE_ELASTICITY)
        
        # Check if B2C sectors have higher elasticities
        high_b2c = self.results[self.results['b2c_share_estimate'] > 0.7]
        low_b2c = self.results[self.results['b2c_share_estimate'] < 0.3]
        
        b2c_ordering_correct = (
            high_b2c['elasticity'].mean() > low_b2c['elasticity'].mean()
        )
        
        validation = {
            'weighted_average_elasticity': round(weighted_avg, 3),
            'benchmark_difference': round(benchmark_diff, 3),
            'b2c_ordering_correct': b2c_ordering_correct,
            'min_elasticity': self.results['elasticity'].min(),
            'max_elasticity': self.results['elasticity'].max(),
            'sectors_analyzed': len(self.results)
        }
        
        print("\nValidation Results:")
        print(f"Weighted average elasticity: {validation['weighted_average_elasticity']}")
        print(f"Difference from UK benchmark (1.0): {validation['benchmark_difference']}")
        print(f"B2C sectors more elastic than B2B: {validation['b2c_ordering_correct']}")
        
        return validation
    
    def export_results(self, output_path: Optional[Path] = None):
        """
        Export calibrated elasticities to CSV.
        """
        if self.results is None:
            self.calibrate_all_sectors()
        
        if output_path is None:
            output_path = Path(__file__).parent / 'sector_vat_elasticities.csv'
        
        # Sort by elasticity for easy review
        export_df = self.results.sort_values('elasticity', ascending=False)
        
        export_df.to_csv(output_path, index=False)
        print(f"\nElasticities exported to: {output_path}")
        
        # Also create summary for labor-intensive services
        labor_intensive = self.identify_labor_intensive_services()
        labor_path = output_path.parent / 'labor_intensive_services.csv'
        labor_intensive.to_csv(labor_path, index=False)
        print(f"Labor-intensive services exported to: {labor_path}")


def main():
    """
    Main execution function.
    """
    print("=" * 60)
    print("SECTOR-SPECIFIC VAT ELASTICITY CALIBRATION")
    print("Based on UK synthetic firm data and literature priors")
    print("=" * 60)
    
    # Initialize calibrator
    calibrator = SectorElasticityCalibrator()
    
    # Load and prepare data
    print("\n1. Loading and analyzing bunching data...")
    sector_data = calibrator.load_and_prepare_data()
    print(f"   Analyzed {len(sector_data)} sectors")
    
    # Calibrate elasticities
    print("\n2. Calibrating sector-specific elasticities...")
    results = calibrator.calibrate_all_sectors()
    
    # Show top bunching sectors
    print("\n3. Top 10 sectors by bunching ratio:")
    top_bunching = results.nlargest(10, 'bunching_ratio')[
        ['sector_name', 'bunching_ratio', 'elasticity', 'confidence']
    ]
    print(top_bunching.to_string(index=False))
    
    # Identify labor-intensive services
    print("\n4. Labor-intensive services (EU definition):")
    labor_intensive = calibrator.identify_labor_intensive_services()
    print(labor_intensive[['sector_name', 'elasticity', 'bunching_ratio']].to_string(index=False))
    
    # Validate
    print("\n5. Validating elasticities...")
    validation = calibrator.validate_elasticities()
    
    # Export results
    print("\n6. Exporting results...")
    calibrator.export_results()
    
    print("\n" + "=" * 60)
    print("CALIBRATION COMPLETE")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    results = main()