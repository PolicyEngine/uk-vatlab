"""
Tests for VAT threshold simulation model.
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vat_simulation import VATSimulator, VATPolicy


class TestVATPolicy:
    """Test VAT policy configuration."""
    
    def test_default_policy(self):
        """Test default UK VAT policy parameters."""
        policy = VATPolicy()
        assert policy.threshold == 90000
        assert policy.standard_rate == 0.20
        assert policy.reduced_rates == {}
        
    def test_custom_policy(self):
        """Test custom VAT policy configuration."""
        policy = VATPolicy(
            threshold=85000,
            standard_rate=0.19,
            reduced_rates={
                (0, 50000): 0.10,  # 10% for firms below £50k
                (50000, 85000): 0.15  # 15% for firms £50k-£85k
            }
        )
        assert policy.threshold == 85000
        assert policy.standard_rate == 0.19
        assert len(policy.reduced_rates) == 2


class TestVATSimulator:
    """Test VAT simulation model."""
    
    @pytest.fixture
    def sample_firms(self):
        """Create sample firm data for testing."""
        np.random.seed(42)
        n = 1000
        return pd.DataFrame({
            'firm_id': range(n),
            'annual_turnover': np.random.lognormal(11, 1.5, n),
            'sector': np.random.choice(['Retail', 'Services'], n),
            'employment': np.random.randint(1, 50, n)
        })
    
    def test_simulator_initialization(self, sample_firms):
        """Test simulator initialization."""
        sim = VATSimulator(sample_firms)
        assert sim.firms is not None
        assert len(sim.firms) == 1000
        assert sim.elasticity_turnover == 0.14  # Default from literature
        
    def test_behavioral_response_bunching(self):
        """Test bunching behavior near threshold."""
        # Create firms near threshold
        firms = pd.DataFrame({
            'firm_id': range(100),
            'annual_turnover': np.linspace(85000, 95000, 100)
        })
        
        sim = VATSimulator(firms, bunching_rate=0.20)
        policy = VATPolicy(threshold=90000)
        
        # Apply behavioral response
        adjusted_firms = sim.apply_behavioral_response(firms.copy(), policy)
        
        # Check bunching below threshold
        near_threshold = adjusted_firms[
            (adjusted_firms['annual_turnover'] >= 88000) & 
            (adjusted_firms['annual_turnover'] < 90000)
        ]
        assert len(near_threshold) > len(firms[
            (firms['annual_turnover'] >= 88000) & 
            (firms['annual_turnover'] < 90000)
        ])
        
    def test_vat_revenue_calculation(self, sample_firms):
        """Test VAT revenue calculation."""
        sim = VATSimulator(sample_firms)
        policy = VATPolicy(threshold=90000, standard_rate=0.20)
        
        results = sim.simulate(policy)
        
        assert 'vat_revenue' in results
        assert 'num_registered' in results
        assert 'behavioral_adjustment' in results
        assert results['vat_revenue'] > 0
        assert results['num_registered'] > 0
        
    def test_marginal_rates_impact(self, sample_firms):
        """Test impact of marginal VAT rates for smaller firms."""
        sim = VATSimulator(sample_firms)
        
        # Policy with reduced rates
        policy_reduced = VATPolicy(
            threshold=90000,
            standard_rate=0.20,
            reduced_rates={(0, 50000): 0.10}
        )
        
        # Policy without reduced rates
        policy_standard = VATPolicy(threshold=90000, standard_rate=0.20)
        
        results_reduced = sim.simulate(policy_reduced)
        results_standard = sim.simulate(policy_standard)
        
        # Reduced rates enable voluntary registration, so could increase revenue
        # Just check that the simulation runs and produces different results
        assert results_reduced['vat_revenue'] != results_standard['vat_revenue']
        assert results_reduced['num_registered'] >= results_standard['num_registered']
        
    def test_threshold_change_impact(self, sample_firms):
        """Test impact of changing VAT threshold."""
        sim = VATSimulator(sample_firms)
        
        # Lower threshold
        policy_low = VATPolicy(threshold=85000)
        results_low = sim.simulate(policy_low)
        
        # Higher threshold
        policy_high = VATPolicy(threshold=95000)
        results_high = sim.simulate(policy_high)
        
        # More firms registered with lower threshold
        assert results_low['num_registered'] > results_high['num_registered']
        # Higher revenue with lower threshold (more firms paying VAT)
        assert results_low['vat_revenue'] > results_high['vat_revenue']
        
    def test_elasticity_sensitivity(self, sample_firms):
        """Test sensitivity to elasticity parameters."""
        # Low elasticity (less responsive)
        sim_low = VATSimulator(sample_firms, elasticity_turnover=0.09)
        # High elasticity (more responsive)
        sim_high = VATSimulator(sample_firms, elasticity_turnover=0.18)
        
        policy = VATPolicy(threshold=90000)
        
        results_low = sim_low.simulate(policy)
        results_high = sim_high.simulate(policy)
        
        # Higher elasticity should lead to larger behavioral response
        assert abs(results_high['behavioral_adjustment']) > abs(results_low['behavioral_adjustment'])