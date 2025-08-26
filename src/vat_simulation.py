"""
VAT threshold simulation model with behavioral responses.

Based on empirical literature:
- Liu et al. (2019): VAT Notches, elasticity 0.09-0.18
- IMF (2024): 1 percentage point growth slowdown near threshold
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class VATPolicy:
    """VAT policy configuration."""
    threshold: float = 90000  # Current UK threshold
    standard_rate: float = 0.20  # 20% standard rate
    reduced_rates: Dict[Tuple[float, float], float] = None  # Marginal rates by turnover band
    
    def __post_init__(self):
        if self.reduced_rates is None:
            self.reduced_rates = {}
    
    def get_effective_rate(self, turnover: float) -> float:
        """Get effective VAT rate for a given turnover level."""
        if turnover < self.threshold:
            # Check for reduced rates
            for (lower, upper), rate in self.reduced_rates.items():
                if lower <= turnover < upper:
                    return rate
            return 0  # Below threshold, no VAT unless voluntary
        return self.standard_rate


class VATSimulator:
    """Simulate VAT threshold effects on firm behavior."""
    
    def __init__(self, 
                 firms: pd.DataFrame,
                 elasticity_turnover: float = 0.14,  # Mid-point from Liu et al.
                 bunching_rate: float = 0.15,  # Proportion bunching near threshold
                 growth_slowdown: float = 0.01):  # 1pp growth slowdown
        """
        Initialize VAT simulator.
        
        Args:
            firms: DataFrame with columns [firm_id, annual_turnover, ...]
            elasticity_turnover: Elasticity of turnover w.r.t. VAT rate (0.09-0.18)
            bunching_rate: Proportion of firms that bunch below threshold
            growth_slowdown: Growth rate reduction near threshold
        """
        self.firms = firms.copy()
        self.elasticity_turnover = elasticity_turnover
        self.bunching_rate = bunching_rate
        self.growth_slowdown = growth_slowdown
        
    def apply_behavioral_response(self, firms: pd.DataFrame, policy: VATPolicy) -> pd.DataFrame:
        """
        Apply behavioral responses to VAT threshold.
        
        Two main effects:
        1. Bunching: Firms near threshold reduce turnover to stay below
        2. Growth effect: Reduced turnover growth due to VAT burden
        """
        adjusted_firms = firms.copy()
        
        # 1. Bunching effect near threshold
        threshold_zone_lower = policy.threshold * 0.95  # 5% below threshold
        threshold_zone_upper = policy.threshold * 1.05  # 5% above threshold
        
        near_threshold = (
            (adjusted_firms['annual_turnover'] >= threshold_zone_lower) &
            (adjusted_firms['annual_turnover'] < threshold_zone_upper)
        )
        
        # Firms that would bunch
        bunching_firms = near_threshold & (
            np.random.random(len(adjusted_firms)) < self.bunching_rate
        )
        
        # Move bunching firms to just below threshold
        if bunching_firms.any():
            # Bunch within 1-2% below threshold
            bunch_point = np.random.uniform(
                policy.threshold * 0.98,
                policy.threshold * 0.995,
                bunching_firms.sum()
            )
            adjusted_firms.loc[bunching_firms, 'annual_turnover'] = bunch_point
        
        # 2. Growth/elasticity effect for registered firms
        registered = adjusted_firms['annual_turnover'] >= policy.threshold
        
        if registered.any():
            # Calculate effective VAT burden
            vat_burden = policy.standard_rate
            
            # Apply elasticity-based adjustment
            # Percentage change in turnover = -elasticity * percentage change in (1-tax rate)
            turnover_response = -self.elasticity_turnover * vat_burden
            
            # Also apply growth slowdown for firms near but above threshold
            just_above = (
                (adjusted_firms['annual_turnover'] >= policy.threshold) &
                (adjusted_firms['annual_turnover'] < policy.threshold * 1.1)
            )
            
            # Reduce turnover based on elasticity
            adjusted_firms.loc[registered, 'annual_turnover'] *= (1 + turnover_response)
            
            # Additional growth slowdown for firms just above threshold
            adjusted_firms.loc[just_above, 'annual_turnover'] *= (1 - self.growth_slowdown)
        
        # 3. Apply marginal rate effects for voluntary registration
        for (lower, upper), rate in policy.reduced_rates.items():
            in_band = (
                (adjusted_firms['annual_turnover'] >= lower) &
                (adjusted_firms['annual_turnover'] < upper)
            )
            if in_band.any():
                # Smaller elasticity response for reduced rates
                response = -self.elasticity_turnover * rate * 0.5  # Assume 50% voluntary registration
                adjusted_firms.loc[in_band, 'annual_turnover'] *= (1 + response)
        
        return adjusted_firms
    
    def calculate_vat_revenue(self, firms: pd.DataFrame, policy: VATPolicy) -> float:
        """Calculate total VAT revenue from firms."""
        revenue = 0
        
        # Standard rate for firms above threshold
        registered = firms['annual_turnover'] >= policy.threshold
        if registered.any():
            # Approximate VAT base as proportion of turnover (assume 50% value-added ratio)
            vat_base = firms.loc[registered, 'annual_turnover'] * 0.5
            revenue += (vat_base * policy.standard_rate).sum()
        
        # Reduced rates for voluntary registration
        for (lower, upper), rate in policy.reduced_rates.items():
            in_band = (
                (firms['annual_turnover'] >= lower) &
                (firms['annual_turnover'] < upper) &
                (~registered)  # Not already counted
            )
            if in_band.any():
                # Assume 40% voluntary registration rate for reduced rate bands
                voluntary_reg_rate = 0.4
                voluntary = in_band & (np.random.random(len(firms)) < voluntary_reg_rate)
                if voluntary.any():
                    vat_base = firms.loc[voluntary, 'annual_turnover'] * 0.5
                    revenue += (vat_base * rate).sum()
        
        return revenue
    
    def simulate(self, policy: VATPolicy) -> Dict:
        """
        Run full simulation with given policy.
        
        Returns:
            Dictionary with simulation results including revenue, 
            number of registered firms, and behavioral adjustments.
        """
        # Baseline (no behavioral response)
        baseline_firms = self.firms.copy()
        baseline_revenue = self.calculate_vat_revenue(baseline_firms, policy)
        baseline_registered = (baseline_firms['annual_turnover'] >= policy.threshold).sum()
        
        # With behavioral response
        adjusted_firms = self.apply_behavioral_response(self.firms.copy(), policy)
        adjusted_revenue = self.calculate_vat_revenue(adjusted_firms, policy)
        adjusted_registered = (adjusted_firms['annual_turnover'] >= policy.threshold).sum()
        
        # Calculate behavioral adjustment (lost revenue due to responses)
        behavioral_adjustment = adjusted_revenue - baseline_revenue
        
        return {
            'vat_revenue': adjusted_revenue,
            'baseline_revenue': baseline_revenue,
            'behavioral_adjustment': behavioral_adjustment,
            'num_registered': adjusted_registered,
            'baseline_registered': baseline_registered,
            'firms_bunching': (
                (adjusted_firms['annual_turnover'] >= policy.threshold * 0.98) &
                (adjusted_firms['annual_turnover'] < policy.threshold)
            ).sum(),
            'adjusted_firms': adjusted_firms,
            'policy': policy
        }
    
    def compare_policies(self, policies: Dict[str, VATPolicy]) -> pd.DataFrame:
        """Compare multiple VAT policies."""
        results = []
        
        for name, policy in policies.items():
            sim_result = self.simulate(policy)
            results.append({
                'policy': name,
                'threshold': policy.threshold,
                'standard_rate': policy.standard_rate,
                'revenue': sim_result['vat_revenue'],
                'registered_firms': sim_result['num_registered'],
                'bunching_firms': sim_result['firms_bunching'],
                'behavioral_cost': -sim_result['behavioral_adjustment']
            })
        
        return pd.DataFrame(results)