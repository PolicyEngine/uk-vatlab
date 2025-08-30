#!/usr/bin/env python3
"""
Synthetic firm data generation for UK business population.

This script generates individual firm records from ONS business structure data,
calibrated to HMRC VAT registration statistics for accurate representation.
"""

import logging
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import torch
from torch import Tensor

logger = logging.getLogger(__name__)


class SyntheticFirmGenerator:
    """
    Synthetic firm data generator for UK business population analysis.
    
    Generates complete UK firm population calibrated to official data sources:
    - ONS data for population structure and employment distribution
    - HMRC data for VAT registration and sector targets
    - Assigns VAT flags to identify HMRC-visible firms
    """
    
    def __init__(
        self,
        device: str = "cpu",
        random_seed: int = 42
    ):
        """Initialize the synthetic firm generator.
        
        Args:
            device: Computing device ('cpu', 'cuda', 'mps')
            random_seed: Random seed for reproducibility
        """
        self.device = device
        self.random_seed = random_seed
        
        # Set random seeds
        torch.manual_seed(random_seed)
        np.random.seed(random_seed)
        
        logger.info(f"Initialized firm generator on device: {device}")
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, int]:
        """Load ONS and HMRC data files from standardized CSV sources.
        
        Returns:
            Tuple containing ONS turnover data, ONS employment data, 
            HMRC turnover bands, HMRC sector data, VAT liability by sector, 
            VAT liability by turnover band, and ONS total firm count
        """
        logger.info("Loading data files...")
        
        # Define paths to data files
        project_root = Path(__file__).parent.parent
        ons_path = project_root / 'data' / 'ONS_UK_business_data' / 'firm_turnover.csv'
        ons_employment_path = project_root / 'data' / 'ONS_UK_business_data' / 'firm_employment.csv'
        hmrc_turnover_path = project_root / 'data' / 'HMRC_VAT_annual_statistics' / 'vat_population_by_turnover_band.csv'
        hmrc_sector_path = project_root / 'data' / 'HMRC_VAT_annual_statistics' / 'vat_population_by_sector.csv'
        vat_liability_sector_path = project_root / 'data' / 'HMRC_VAT_annual_statistics' / 'vat_liability_by_sector.csv'
        vat_liability_band_path = project_root / 'data' / 'HMRC_VAT_annual_statistics' / 'vat_liability_by_turnover_band.csv'
        
        # Load CSV files
        ons_df = pd.read_csv(ons_path)
        ons_employment_df = pd.read_csv(ons_employment_path)
        hmrc_turnover_df = pd.read_csv(hmrc_turnover_path)
        hmrc_sector_df = pd.read_csv(hmrc_sector_path)
        vat_liability_sector_df = pd.read_csv(vat_liability_sector_path)
        vat_liability_band_df = pd.read_csv(vat_liability_band_path)
        
        logger.info(f"Loaded ONS turnover data: {len(ons_df)} rows")
        logger.info(f"Loaded ONS employment data: {len(ons_employment_df)} rows")
        logger.info(f"Loaded HMRC turnover data: {len(hmrc_turnover_df)} rows")
        logger.info(f"Loaded HMRC sector data: {len(hmrc_sector_df)} rows")
        logger.info(f"Loaded VAT liability by sector data: {len(vat_liability_sector_df)} rows")
        logger.info(f"Loaded VAT liability by band data: {len(vat_liability_band_df)} rows")
        
        # Extract ONS total
        ons_total_row = ons_df[ons_df['SIC Code'].isna() | (ons_df['SIC Code'] == '')]
        if len(ons_total_row) > 0:
            ons_total = ons_total_row.iloc[0]['Total']
        else:
            sector_rows = ons_df[~ons_df['Description'].str.contains('Total', na=False)]
            ons_total = sector_rows['Total'].sum()
        
        logger.info(f"ONS total firms: {ons_total:,}")
        
        return ons_df, ons_employment_df, hmrc_turnover_df, hmrc_sector_df, vat_liability_sector_df, vat_liability_band_df, ons_total
    
    def generate_base_firms(self, ons_df: pd.DataFrame) -> Tuple[Tensor, Tensor]:
        """Generate base firm records using efficient batch processing.
        
        Args:
            ons_df: ONS turnover data
            
        Returns:
            Tuple of (sic_codes, turnover_values)
        """
        logger.info("Generating base firms using efficient batch processing...")
        
        # ONS turnover band parameters (min, max, midpoint in £k)
        band_params = {
            '0-49': (0, 49, 24.5),
            '50-99': (50, 99, 74.5),
            '100-249': (100, 249, 174.5),
            '250-499': (250, 499, 374.5),
            '500-999': (500, 999, 749.5),
            '1000-4999': (1000, 4999, 2999.5),
            '5000+': (5000, 50000, 15000)
        }
        
        all_sic_codes = []
        all_turnovers = []
        
        # Process each sector
        for _, row in ons_df.iterrows():
            sic_code = row['SIC Code']
            
            # Skip summary rows
            if pd.isna(sic_code) or sic_code == '' or sic_code == 'Total':
                continue
            
            sic_formatted = str(int(sic_code)).zfill(5)
            
            # Generate firms for each turnover band
            for band, (min_val, max_val, midpoint) in band_params.items():
                if band in row and pd.notna(row[band]) and row[band] > 0:
                    count = int(row[band])
                    
                    if count > 0:
                        # Generate turnover values with noise smoothing
                        turnovers = self._generate_turnover_values(
                            band, count, min_val, max_val, midpoint
                        )
                        
                        # Store results
                        all_sic_codes.extend([sic_formatted] * count)
                        all_turnovers.extend(turnovers.cpu().numpy())
        
        # Convert to efficient data structures
        sic_codes_tensor = torch.tensor([int(sic) for sic in all_sic_codes], 
                                       dtype=torch.int64, device=self.device)
        turnover_tensor = torch.tensor(all_turnovers, 
                                      dtype=torch.float32, device=self.device)
        
        logger.info(f"Generated {len(all_sic_codes):,} base firms")
        
        return sic_codes_tensor, turnover_tensor
    
    def _generate_turnover_values(self, band_name: str, firm_count: int, 
                                        min_turnover: float, max_turnover: float, 
                                        midpoint_turnover: float) -> Tensor:
        """Generate turnover values within a band with noise smoothing.
        
        Args:
            band_name: ONS turnover band name (e.g., '0-49', '50-99')
            firm_count: Number of firms to generate in this band
            min_turnover: Minimum turnover value (£k)
            max_turnover: Maximum turnover value (£k)  
            midpoint_turnover: Midpoint turnover for distribution (£k)
            
        Returns:
            Generated turnover values with noise smoothing applied
        """
        if firm_count == 0:
            return torch.empty(0, device=self.device)
        
        # Generate turnover values with noise smoothing across the full band range
        band_width = max_turnover - min_turnover
        
        # Use uniform noise for distribution smoothing
        noise_std = max(25.0, band_width * 0.2)  # Uniform noise: 25k minimum or 20% of band width
        
        # Generate uniform base values across the full band range
        uniform_values = torch.rand(firm_count, device=self.device)
        base_turnover_values = min_turnover + uniform_values * band_width
        
        # Add Gaussian noise for smoothing
        noise = torch.normal(0, noise_std, (firm_count,), device=self.device)
        turnover_values = base_turnover_values + noise
        
        # Ensure all turnover values are positive
        turnover_values = torch.clamp(turnover_values, min=0.1)
        
        return turnover_values
    
    def assign_vat_registration_flags(self, turnover_values: Tensor, hmrc_bands: Dict[str, int]) -> Tensor:
        """Assign VAT registration flags to identify HMRC-visible firms.
        
        VAT registration triggers:
        1. Mandatory: Annual turnover > £85k
        2. Voluntary: Random subset of firms below threshold (calculated from HMRC data)
        
        Args:
            turnover_values: Array of turnover values
            hmrc_bands: HMRC band data to calculate voluntary rate
            
        Returns:
            Boolean array indicating VAT registration status
        """
        logger.info("Assigning VAT registration flags...")
        
        # Calculate voluntary VAT rate from Target/Synthetic ratio for £1_to_Threshold
        hmrc_target_1_to_threshold = hmrc_bands['£1_to_Threshold']  # HMRC target: 678,350
        synthetic_1_to_threshold = ((turnover_values > 0) & (turnover_values <= 85.0)).sum().item()  # Current synthetic count
        voluntary_rate = hmrc_target_1_to_threshold / synthetic_1_to_threshold if synthetic_1_to_threshold > 0 else 0.15
        
        logger.info(f"Calculated voluntary VAT rate: {voluntary_rate:.3f} (Target: {hmrc_target_1_to_threshold:,} / Synthetic: {synthetic_1_to_threshold:,})")
        
        # Mandatory registration above threshold
        mandatory_vat = turnover_values > 85.0
        
        # Voluntary registration below threshold (but above 0)
        below_threshold = (turnover_values > 0) & (turnover_values <= 85.0)
        n_below_threshold = below_threshold.sum().item()
        
        if n_below_threshold > 0:
            # Random selection for voluntary VAT registration using calculated rate
            voluntary_mask = torch.rand(len(turnover_values), device=self.device) < voluntary_rate
            voluntary_vat = below_threshold & voluntary_mask
        else:
            voluntary_vat = torch.zeros_like(below_threshold)
        
        vat_registered = mandatory_vat | voluntary_vat
        
        logger.info(f"VAT registration: {mandatory_vat.sum():.0f} mandatory + {voluntary_vat.sum():.0f} voluntary = {vat_registered.sum():.0f} total")
        logger.info(f"Non-VAT registered: {(~vat_registered).sum():.0f} firms")
        
        return vat_registered
    
    def create_comprehensive_target_matrix(self, turnover_values: Tensor, sic_codes: Tensor, input_values: Tensor,
                                      hmrc_bands: Dict[str, int], hmrc_sector_df: pd.DataFrame, ons_employment_df: pd.DataFrame, 
                                      vat_liability_sector_df: pd.DataFrame, vat_liability_band_df: pd.DataFrame, ons_total: int) -> Tuple[Tensor, Tensor]:
        """Create comprehensive target matrix for calibration.
        
        Creates targets for all HMRC turnover bands, sector targets, and VAT liability targets.
        The optimization will determine which firms contribute to which targets 
        based on VAT registration flags.
        
        Args:
            turnover_values: Array of turnover values
            sic_codes: Array of SIC codes
            input_values: Array of input values
            hmrc_bands: Dictionary of all HMRC targets by band
            hmrc_sector_df: HMRC sector data for ratio targets
            ons_employment_df: ONS employment data for ratio targets
            vat_liability_sector_df: VAT liability data by sector
            vat_liability_band_df: VAT liability data by turnover band
            ons_total: Total firm count target from ONS
            
        Returns:
            Tuple of (target_matrix, target_values)
        """
        logger.info("Creating comprehensive target matrix for calibration...")
        
        n_firms = len(turnover_values)
        # Get sector data and calculate ratios
        sector_rows = hmrc_sector_df[hmrc_sector_df['Trade_Sector'] != 'Total'].copy()
        hmrc_total = hmrc_sector_df[hmrc_sector_df['Trade_Sector'] == 'Total']['2023-24'].iloc[0]
        n_sectors = len(sector_rows)
        
        # Get VAT liability sector data (excluding total)
        vat_liability_sector_rows = vat_liability_sector_df[vat_liability_sector_df['Trade_Sector'] != 'Total'].copy()
        n_vat_sectors = len(vat_liability_sector_rows)
        
        # Get VAT liability by turnover band data
        vat_liability_band_latest = vat_liability_band_df.iloc[-1]  # Get 2023-24 data
        vat_liability_bands = {
            'Negative_or_Zero': vat_liability_band_latest['Negative_or_Zero'],
            '£1_to_Threshold': vat_liability_band_latest['£1_to_Threshold'],
            '£Threshold_to_£150k': vat_liability_band_latest['£Threshold_to_£150k'],
            '£150k_to_£300k': vat_liability_band_latest['£150k_to_£300k'],
            '£300k_to_£500k': vat_liability_band_latest['£300k_to_£500k'],
            '£500k_to_£1m': vat_liability_band_latest['£500k_to_£1m'],
            '£1m_to_£10m': vat_liability_band_latest['£1m_to_£10m'],
            'Greater_than_£10m': vat_liability_band_latest['Greater_than_£10m']
        }
        n_vat_bands = 7  # Number of VAT liability bands (excluding Total and Negative_or_Zero)
        
        # Get employment data and calculate ratios
        emp_bands = ['0-4', '5-9', '10-19', '20-49', '50-99', '100-249', '250+']
        n_employment_bands = len(emp_bands)
        
        n_targets = 7 + n_sectors + n_employment_bands + n_vat_sectors + n_vat_bands  # 7 turnover + sector + employment + VAT liability by sector + VAT liability by band
        
        # Initialize target matrix  
        target_matrix = torch.zeros(n_targets, n_firms, device=self.device)
        
        # Map all firms to HMRC bands
        all_band_indices = self._map_to_hmrc_bands(turnover_values)
        
        # Rows 0-6: Turnover band targets
        # Row 0: £1_to_Threshold - keep ONS structure
        firms_in_threshold = (all_band_indices == 1)
        target_matrix[0, firms_in_threshold] = 1.0
        
        # Row 1: £Threshold_to_£150k - calibrate to HMRC target  
        firms_150k = (all_band_indices == 2)
        target_matrix[1, firms_150k] = 1.0
        
        # Rows 2-6: Individual HMRC bands above £150k
        for i, band_idx in enumerate([3, 4, 5, 6, 7], start=2):  # £150k_to_£300k, etc.
            firms_in_band = (all_band_indices == band_idx)
            target_matrix[i, firms_in_band] = 1.0
        
        # Rows 7 to 7+n_sectors-1: Sector targets (for VAT-registered firms only)
        for i, (_, sector_row) in enumerate(sector_rows.iterrows(), start=7):
            trade_sector = sector_row['Trade_Sector']
            # Convert HMRC Trade_Sector to SIC code (00001 -> 1, 00002 -> 2, etc.)
            sic_code = int(trade_sector)
            
            # Find firms in this sector
            firms_in_sector = (sic_codes == sic_code)
            target_matrix[i, firms_in_sector] = 1.0
        
        # Generate employment assignments for target matrix (temporary assignments for optimization)
        employment_values = self.assign_employment(n_firms, ons_employment_df)
        
        # Map employment to bands
        def map_employment_to_band_idx(emp_val):
            if emp_val <= 4:
                return 0  # '0-4'
            elif emp_val <= 9:
                return 1  # '5-9'
            elif emp_val <= 19:
                return 2  # '10-19'
            elif emp_val <= 49:
                return 3  # '20-49'
            elif emp_val <= 99:
                return 4  # '50-99'
            elif emp_val <= 249:
                return 5  # '100-249'
            else:
                return 6  # '250+'
        
        employment_band_indices = torch.tensor([map_employment_to_band_idx(emp.item()) for emp in employment_values], 
                                             dtype=torch.long, device=self.device)
        
        # Rows 7+n_sectors to 7+n_sectors+n_employment_bands-1: Employment ratio targets  
        emp_start_row = 7 + n_sectors
        for band_idx, _ in enumerate(emp_bands):
            row_idx = emp_start_row + band_idx
            firms_in_emp_band = (employment_band_indices == band_idx)
            target_matrix[row_idx, firms_in_emp_band] = 1.0
        
        # Calculate VAT liability for each firm (output - input)
        vat_liability_values = turnover_values - input_values  # in £k
        
        # Rows 7+n_sectors+n_employment_bands to 7+n_sectors+n_employment_bands+n_vat_sectors-1: VAT liability targets by sector
        vat_start_row = 7 + n_sectors + n_employment_bands
        for i, (_, vat_row) in enumerate(vat_liability_sector_rows.iterrows()):
            row_idx = vat_start_row + i
            sic_code = int(vat_row['Trade_Sector'])
            
            # Find firms in this sector and calculate their VAT liability contribution
            firms_in_sector = (sic_codes == sic_code)
            # Weight by VAT liability for this sector's target
            target_matrix[row_idx, firms_in_sector] = vat_liability_values[firms_in_sector]
        
        # Rows 7+n_sectors+n_employment_bands+n_vat_sectors to end: VAT liability targets by turnover band (excluding Negative_or_Zero)
        vat_band_start_row = 7 + n_sectors + n_employment_bands + n_vat_sectors
        for i, band_name in enumerate(['£1_to_Threshold', '£Threshold_to_£150k', 
                                       '£150k_to_£300k', '£300k_to_£500k', '£500k_to_£1m', 
                                       '£1m_to_£10m', 'Greater_than_£10m']):
            row_idx = vat_band_start_row + i
            
            # Map firms to this turnover band
            if band_name == '£1_to_Threshold':
                firms_in_band = (turnover_values > 0) & (turnover_values <= 85)
            elif band_name == '£Threshold_to_£150k':
                firms_in_band = (turnover_values > 85) & (turnover_values <= 150)
            elif band_name == '£150k_to_£300k':
                firms_in_band = (turnover_values > 150) & (turnover_values <= 300)
            elif band_name == '£300k_to_£500k':
                firms_in_band = (turnover_values > 300) & (turnover_values <= 500)
            elif band_name == '£500k_to_£1m':
                firms_in_band = (turnover_values > 500) & (turnover_values <= 1000)
            elif band_name == '£1m_to_£10m':
                firms_in_band = (turnover_values > 1000) & (turnover_values <= 10000)
            else:  # Greater_than_£10m
                firms_in_band = turnover_values > 10000
            
            # Weight by VAT liability for this band's target
            target_matrix[row_idx, firms_in_band] = vat_liability_values[firms_in_band]
        
        # Calculate targets
        # £1_to_Threshold: Use ONS structure (current count from generation)
        ons_threshold_count = firms_in_threshold.sum().item()
        
        # Turnover band targets (absolute numbers)
        turnover_targets = [
            ons_threshold_count,                     # £1_to_Threshold: Keep ONS structure
            hmrc_bands['£Threshold_to_£150k'],       # £Threshold_to_£150k: HMRC
            hmrc_bands['£150k_to_£300k'],            # £150k_to_£300k: HMRC
            hmrc_bands['£300k_to_£500k'],            # £300k_to_£500k: HMRC
            hmrc_bands['£500k_to_£1m'],              # £500k_to_£1m: HMRC
            hmrc_bands['£1m_to_£10m'],               # £1m_to_£10m: HMRC
            hmrc_bands['Greater_than_£10m']          # Greater_than_£10m: HMRC
        ]
        
        # Sector targets (direct HMRC targets for VAT-registered firms)
        sector_targets = []
        for _, sector_row in sector_rows.iterrows():
            sector_count = sector_row['2023-24']  # Direct HMRC target
            sector_targets.append(sector_count)
        
        # Employment count targets (direct ONS employment counts)
        employment_targets = []
        # Get ONS employment totals
        ons_emp_totals = {}
        for band in emp_bands:
            if band in ons_employment_df.columns:
                sector_rows_emp = ons_employment_df[~ons_employment_df['Description'].str.contains('Total', na=False)]
                ons_emp_totals[band] = sector_rows_emp[band].fillna(0).sum()
            else:
                ons_emp_totals[band] = 0
        
        # Use direct ONS employment counts as targets
        for band in emp_bands:
            emp_count = ons_emp_totals[band]
            employment_targets.append(emp_count)
        
        # VAT liability targets by sector (in millions £, convert to £k)
        vat_liability_sector_targets = []
        for _, vat_row in vat_liability_sector_rows.iterrows():
            vat_liability_millions = vat_row['2023-24']  # in millions £
            vat_liability_k = vat_liability_millions * 1000  # convert to £k
            vat_liability_sector_targets.append(vat_liability_k)
        
        # VAT liability targets by turnover band (in millions £, convert to £k) - excluding Negative_or_Zero
        vat_liability_band_targets = []
        for band_name in ['£1_to_Threshold', '£Threshold_to_£150k', 
                          '£150k_to_£300k', '£300k_to_£500k', '£500k_to_£1m', 
                          '£1m_to_£10m', 'Greater_than_£10m']:
            vat_liability_millions = vat_liability_bands[band_name]  # in millions £
            vat_liability_k = vat_liability_millions * 1000  # convert to £k
            vat_liability_band_targets.append(vat_liability_k)
        
        target_values_list = turnover_targets + sector_targets + employment_targets + vat_liability_sector_targets + vat_liability_band_targets
        
        target_values = torch.tensor(
            target_values_list, 
            dtype=torch.float32, device=self.device
        )
        
        logger.info(f"Target matrix shape: {target_matrix.shape}")
        logger.info(f"Calibration targets (turnover + sector + employment):")
        
        # Log turnover targets
        turnover_names = ['£1_to_Threshold (ONS)', '£Threshold_to_£150k (HMRC)', 
                         '£150k_to_£300k (HMRC)', '£300k_to_£500k (HMRC)', 
                         '£500k_to_£1m (HMRC)', '£1m_to_£10m (HMRC)', 'Greater_than_£10m (HMRC)']
        for target_name, target_val in zip(turnover_names, turnover_targets):
            logger.info(f"  {target_name}: {target_val:,.0f}")
        
        # Log sector and employment targets (summary)
        logger.info(f"  Sector targets: {n_sectors} sectors from HMRC data (VAT-registered)")
        logger.info(f"  Employment count targets: {n_employment_bands} bands from ONS data (direct counts)")
        logger.info(f"  VAT liability sector targets: {n_vat_sectors} sectors from HMRC data (in £millions)")
        logger.info(f"  VAT liability band targets: {n_vat_bands} bands from HMRC data (in £millions, 2x weight)")
        logger.info(f"  Total targets: {len(target_values_list)} (7 turnover + {n_sectors} sector + {n_employment_bands} employment + {n_vat_sectors} VAT liability sector + {n_vat_bands} VAT liability band)")
        logger.info(f"  Negative_or_Zero: MANUAL (ONS doesn't have them)")
        
        return target_matrix, target_values
    
    def optimize_weights(self, target_matrix: Tensor, target_values: Tensor,
                               n_iterations: int = 300, lr: float = 0.01) -> Tensor:
        """Optimize weights to match multiple targets simultaneously.
        
        Uses symmetric relative error loss for robust calibration.
        
        Args:
            target_matrix: Matrix where A[i,j] = contribution of firm j to target i
            target_values: Vector of target values to match
            n_iterations: Number of optimization iterations
            lr: Learning rate
            
        Returns:
            Optimized weights
        """
        logger.info("Starting multi-objective weight optimization...")
        
        _, n_firms = target_matrix.shape
        
        # Initialize log-weights (ensures positive weights)
        log_weights = torch.zeros(n_firms, device=self.device, requires_grad=True)
        optimizer = torch.optim.Adam([log_weights], lr=lr)
        
        best_loss = float('inf')
        patience = 100
        patience_counter = 0
        
        for iteration in range(n_iterations):
            optimizer.zero_grad()
            
            # Convert to positive weights
            weights = torch.exp(log_weights)
            
            # Apply 15% dropout during training
            if log_weights.requires_grad:  # Only during training
                dropout_mask = torch.rand_like(weights) > 0.05  # Keep 95%, drop 15%
                weights = weights * dropout_mask
            
            # Calculate predictions: target_matrix @ weights
            predictions = torch.matmul(target_matrix, weights)
            
            # Symmetric relative error loss (robust to different target scales)
            epsilon = 1e-6
            pred_adj = predictions + epsilon
            target_adj = target_values + epsilon
            
            # Symmetric relative error: min(|pred/target - 1|^2, |target/pred - 1|^2)
            error_1 = ((pred_adj / target_adj) - 1) ** 2
            error_2 = ((target_adj / pred_adj) - 1) ** 2
            sre_loss = torch.minimum(error_1, error_2)
            
            # Apply importance weights based on target type
            importance_weights = torch.ones_like(sre_loss)
            importance_weights[:7] = 5.0  # 5x weight for turnover targets
            
            # Calculate indices for different target types
            # Structure: 7 turnover + n_sectors + n_employment_bands + n_vat_sectors + n_vat_bands
            n_total_targets = len(sre_loss)
            
            # We need to dynamically calculate the section sizes from the actual target matrix
            # For now, use fixed estimates based on typical data structure
            n_employment = 7  # Fixed: 7 employment bands
            
            # The remaining targets are split between sectors and VAT liability
            n_remaining = n_total_targets - 7 - n_employment  # Remove turnover and employment
            n_est_sectors = n_remaining // 3  # Rough estimate (sectors, vat_sectors, vat_bands)
            n_est_vat_sectors = n_est_sectors
            n_est_vat_bands = n_remaining - n_est_sectors - n_est_vat_sectors
            
            sector_start_idx = 7
            emp_start_idx = 7 + n_est_sectors
            vat_sector_start_idx = emp_start_idx + n_employment
            vat_band_start_idx = vat_sector_start_idx + n_est_vat_sectors
            
            # Set importance weights
            importance_weights[sector_start_idx:emp_start_idx] = 1.0  # 1x weight for sector targets
            importance_weights[emp_start_idx:vat_sector_start_idx] = 1.0  # 1x weight for employment targets
            importance_weights[vat_sector_start_idx:vat_band_start_idx] = 1.0  # 1x weight for VAT liability sector targets
            importance_weights[vat_band_start_idx:] = 2.0  # 2x weight for VAT liability band targets
            
            weighted_loss = sre_loss * importance_weights
            total_loss = torch.mean(weighted_loss)
            
            # Add regularization to prevent extreme weights
            reg_loss = 0.01 * torch.mean(torch.abs(log_weights))
            total_loss += reg_loss
            
            total_loss.backward()
            
            # Gradient clipping for stability
            torch.nn.utils.clip_grad_norm_([log_weights], max_norm=1.0)
            
            optimizer.step()
            
            # Early stopping
            if total_loss.item() < best_loss:
                best_loss = total_loss.item()
                patience_counter = 0
            else:
                patience_counter += 1
            
            if iteration % 100 == 0:
                logger.info(f"Iteration {iteration}: Loss = {total_loss.item():.6f}")
            
            if patience_counter > patience:
                logger.info(f"Early stopping at iteration {iteration}")
                break
        
        final_weights = torch.exp(log_weights)
        final_predictions = torch.matmul(target_matrix, final_weights)
        
        logger.info("Optimization complete:")
        target_names = ['Negative_or_Zero', '£1_to_Threshold', '£Threshold_to_£150k', '£150k_to_£300k', 
                       '£300k_to_£500k', '£500k_to_£1m', '£1m_to_£10m', 'Greater_than_£10m']
        for i, (pred, target, name) in enumerate(zip(final_predictions, target_values, target_names)):
            if target > 0:  # Only log targets we're actually trying to match
                accuracy = 1 - abs(pred - target) / target
                logger.info(f"  {name}: {pred:.0f} vs {target:.0f} ({accuracy:.1%})")
            else:
                logger.info(f"  {name}: SKIPPED (pred: {pred:.0f})")
        
        return final_weights.detach()
    
    def apply_final_calibration(self, base_sic_codes: Tensor, base_turnover: Tensor, base_input: Tensor,
                                     weights_tensor: Tensor, hmrc_bands: Dict[str, int]) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
        """Apply final calibration adjustments.
        
        Key calibration steps:
        1. Keep ALL base firms (no sampling)
        2. Add zero/negative turnover firms manually
        3. Apply calibration weights to match targets
        
        Args:
            base_sic_codes: Original base SIC codes
            base_turnover: Original base turnover values
            base_input: Original base input values
            weights_tensor: Calibration weights from optimization
            hmrc_bands: HMRC target bands
            
        Returns:
            Tuple of final (sic_codes, turnover, input, weights) tensors
        """
        logger.info("Applying final calibration adjustments...")
        
        all_final_firms = []
        
        # Step 1: Add ALL base firms with their weights
        hmrc_band_indices = self._map_to_hmrc_bands(base_turnover)
        
        logger.info(f"Adding {len(base_sic_codes):,} base firms...")
        for i in range(len(base_sic_codes)):
            band_idx = hmrc_band_indices[i].item()
            
            # Use calibrated weights from optimization for all bands
            weight = weights_tensor[i].item()
            
            all_final_firms.append({
                'sic_code': base_sic_codes[i].item(),
                'annual_turnover_k': base_turnover[i].item(),
                'annual_input_k': base_input[i].item(),
                'weight': weight
            })
        
        # Step 2: Manually add zero/negative turnover firms
        negative_zero_target = hmrc_bands['Negative_or_Zero']
        
        if negative_zero_target > 0:
            # Get current sector distribution for proportional allocation
            unique_sics, counts = torch.unique(base_sic_codes, return_counts=True)
            total_current_firms = len(base_sic_codes)
            
            logger.info(f"Manually adding {negative_zero_target:,} zero turnover firms from HMRC...")
            zero_firms_count = 0
            
            for sic, count in zip(unique_sics, counts):
                sector_weight = count.float() / total_current_firms
                firms_for_sector = int((negative_zero_target * sector_weight).item())
                if firms_for_sector > 0:
                    for _ in range(firms_for_sector):
                        all_final_firms.append({
                            'sic_code': sic.item(),
                            'annual_turnover_k': 0.0,
                            'annual_input_k': 0.0,
                            'weight': 1.0
                        })
                        zero_firms_count += 1
            
            logger.info(f"Added {zero_firms_count:,} firms with zero turnover")
        
        # Convert back to tensors
        if all_final_firms:
            final_sics = torch.tensor([f['sic_code'] for f in all_final_firms], 
                                    dtype=torch.int64, device=self.device)
            final_turnover = torch.tensor([f['annual_turnover_k'] for f in all_final_firms], 
                                        dtype=torch.float32, device=self.device)
            final_input = torch.tensor([f['annual_input_k'] for f in all_final_firms],
                                     dtype=torch.float32, device=self.device)
            final_weights = torch.tensor([f['weight'] for f in all_final_firms], 
                                       dtype=torch.float32, device=self.device)
            
            logger.info(f"Final dataset: {len(all_final_firms):,} firms")
            logger.info(f"Total weighted population: {final_weights.sum():.0f}")
        else:
            # Empty tensors if no firms generated
            final_sics = torch.empty(0, dtype=torch.int64, device=self.device)
            final_turnover = torch.empty(0, dtype=torch.float32, device=self.device)
            final_input = torch.empty(0, dtype=torch.float32, device=self.device)
            final_weights = torch.empty(0, dtype=torch.float32, device=self.device)
        
        return final_sics, final_turnover, final_input, final_weights
    
    def _map_to_hmrc_bands(self, turnover_values: Tensor) -> Tensor:
        """Map turnover values to HMRC band indices.
        
        Args:
            turnover_values: Array of turnover values
            
        Returns:
            HMRC band indices (0-7 for 8 HMRC bands)
        """
        # Initialize with highest band (Greater_than_£10m = 7)
        band_indices = torch.full_like(turnover_values, 7, dtype=torch.long)
        
        # Assign bands based on turnover thresholds
        band_indices = torch.where(turnover_values <= 0, 0, band_indices)  # Negative_or_Zero
        band_indices = torch.where((turnover_values > 0) & (turnover_values <= 85), 1, band_indices)  # £1_to_Threshold
        band_indices = torch.where((turnover_values > 85) & (turnover_values <= 150), 2, band_indices)  # £Threshold_to_£150k
        band_indices = torch.where((turnover_values > 150) & (turnover_values <= 300), 3, band_indices)  # £150k_to_£300k
        band_indices = torch.where((turnover_values > 300) & (turnover_values <= 500), 4, band_indices)  # £300k_to_£500k
        band_indices = torch.where((turnover_values > 500) & (turnover_values <= 1000), 5, band_indices)  # £500k_to_£1m
        band_indices = torch.where((turnover_values > 1000) & (turnover_values <= 10000), 6, band_indices)  # £1m_to_£10m
        
        return band_indices
    
    def _print_validation_section(self, title: str, width: int = 65):
        """Print a formatted validation section header."""
        print(f"\n{title}:")
        print("-" * width)
    
    def _print_accuracy_breakdown(self, accuracies: list, n_items: int, label: str):
        """Print standardized accuracy breakdown."""
        accuracy_95_plus = sum(1 for acc in accuracies if acc >= 0.95)
        accuracy_90_95 = sum(1 for acc in accuracies if 0.90 <= acc < 0.95)
        accuracy_80_90 = sum(1 for acc in accuracies if 0.80 <= acc < 0.90)
        accuracy_below_80 = sum(1 for acc in accuracies if acc < 0.80)
        
        overall_accuracy = np.mean(accuracies) if accuracies else 0.0
        print(f"{label} OVERALL ACCURACY: {overall_accuracy:.1%}")
        print(f"Accuracy breakdown: ≥95%: {accuracy_95_plus}/{n_items}, "
              f"90-95%: {accuracy_90_95}/{n_items}, "
              f"80-90%: {accuracy_80_90}/{n_items}, "
              f"<80%: {accuracy_below_80}/{n_items}")
        return overall_accuracy
    
    def generate_input_values(self, turnover_values: Tensor, sic_codes: Tensor) -> Tensor:
        """Generate input values for firms directly from distributions.
        
        Input values are drawn from beta distributions that allow for:
        - Most firms: inputs 60-95% of turnover (positive VAT liability)
        - Some firms: inputs > turnover (negative VAT liability)
        
        Args:
            turnover_values: Array of turnover values (output)
            sic_codes: Array of SIC codes (used for sector-specific variations)
            
        Returns:
            Array of input values in £k
        """
        logger.info("Generating input values for firms from distributions...")
        
        n_firms = len(turnover_values)
        input_values = torch.zeros_like(turnover_values)
        
        # Generate input/output ratios from a beta distribution
        # Beta(4, 2) gives a distribution centered around 0.67 with range [0, 1]
        # We'll scale and shift this to get our desired range
        alpha, beta = 4.0, 2.0
        base_ratios = torch.distributions.Beta(alpha, beta).sample((n_firms,)).to(self.device)
        
        # Scale to range [0.3, 1.3] to allow both positive and negative VAT liability
        # Most values will be in [0.6, 0.95] range
        scaled_ratios = 0.3 + base_ratios * 1.0  # Maps [0,1] to [0.3, 1.3]
        
        # Add sector-specific noise
        sector_noise = torch.randn(n_firms, device=self.device) * 0.15
        
        # For some sectors, shift the distribution to make negative liability more likely
        for i in range(n_firms):
            sic = sic_codes[i].item()
            
            # Add extra variation for certain sectors that tend to have extreme values
            if sic in [1, 3, 6, 7, 9, 10, 24, 30, 36, 37, 49, 50, 51, 60, 64, 79, 84]:
                # These sectors often have negative VAT liability
                # Add positive bias to input ratio
                scaled_ratios[i] += torch.rand(1, device=self.device).item() * 0.3
            elif sic in [11, 12, 69, 70, 78]:
                # These sectors often have high VAT liability (low inputs)
                # Add negative bias to input ratio
                scaled_ratios[i] -= torch.rand(1, device=self.device).item() * 0.2
        
        # Apply ratios with noise
        final_ratios = torch.clamp(scaled_ratios + sector_noise, 0.1, 1.5)
        
        # Generate input values
        for i in range(n_firms):
            if turnover_values[i] <= 0:
                input_values[i] = 0
            else:
                input_values[i] = turnover_values[i] * final_ratios[i]
        
        logger.info(f"Generated input values for {n_firms:,} firms")
        logger.info(f"Input/output ratio statistics:")
        logger.info(f"  Mean: {final_ratios.mean():.2%}")
        logger.info(f"  Std: {final_ratios.std():.2%}")
        logger.info(f"  Min: {final_ratios.min():.2%}")
        logger.info(f"  Max: {final_ratios.max():.2%}")
        logger.info(f"  Firms with negative VAT liability (input > output): {(final_ratios > 1.0).sum().item():,}")
        
        return input_values
    
    def assign_employment(self, num_firms: int, 
                               ons_employment_df: pd.DataFrame) -> Tensor:
        """Assign employment using ONS distribution.
        
        Args:
            num_firms: Number of firms to assign employment to
            ons_employment_df: ONS employment data
            
        Returns:
            Array of employment values
        """
        logger.info("Assigning employment using ONS distribution...")
        
        # Employment bands and parameters
        emp_bands = ['0-4', '5-9', '10-19', '20-49', '50-99', '100-249', '250+']
        band_params = {
            '0-4': (1, 4, 2.5),
            '5-9': (5, 9, 7),
            '10-19': (10, 19, 14.5),
            '20-49': (20, 49, 34.5),
            '50-99': (50, 99, 74.5),
            '100-249': (100, 249, 174.5),
            '250+': (250, 2000, 400)
        }
        
        # Calculate ONS employment band totals
        total_ons_counts = {}
        for band in emp_bands:
            if band in ons_employment_df.columns:
                sector_rows = ons_employment_df[~ons_employment_df['Description'].str.contains('Total', na=False)]
                total_ons_counts[band] = int(sector_rows[band].fillna(0).sum())
            else:
                total_ons_counts[band] = 0
        
        total_ons_firms = sum(total_ons_counts.values())
        
        # Calculate target counts for each band
        employment_values = []
        for band in emp_bands:
            target_count = int(round(num_firms * total_ons_counts[band] / total_ons_firms))
            if target_count > 0:
                min_val, max_val, midpoint = band_params[band]
                
                # Generate employment values
                if band == '0-4':
                    # Uniform for micro businesses
                    values = torch.randint(1, 5, (target_count,), device=self.device)
                elif band == '250+':
                    # Log-normal for large firms
                    log_mean = torch.log(torch.tensor(midpoint, device=self.device))
                    values = torch.normal(log_mean, 0.8, (target_count,), device=self.device).exp()
                    values = torch.clamp(values, min_val, max_val).round()
                else:
                    # Beta distribution for others
                    uniform = torch.rand(target_count, device=self.device)
                    beta_values = uniform.pow(0.5) * (1 - uniform).pow(2.0)  # Beta approximation
                    values = min_val + beta_values * (max_val - min_val)
                    values = values.round()
                
                employment_values.extend(values.cpu().numpy())
        
        # Shuffle and pad/trim to exact size
        np.random.shuffle(employment_values)
        if len(employment_values) < num_firms:
            employment_values.extend([1] * (num_firms - len(employment_values)))
        elif len(employment_values) > num_firms:
            employment_values = employment_values[:num_firms]
        
        employment_array = torch.tensor(employment_values, 
                                       dtype=torch.float32, device=self.device)
        
        logger.info(f"Assigned employment to {num_firms:,} firms")
        
        return employment_array
    
    def validate_comprehensive_accuracy(self, synthetic_df: pd.DataFrame, hmrc_target_bands: Dict[str, int],
                                       ons_total_target: int, ons_employment_df: pd.DataFrame, 
                                       hmrc_sector_df: pd.DataFrame, vat_liability_df: pd.DataFrame, 
                                       vat_liability_band_df: pd.DataFrame) -> Tuple[float, float, float, float, float, float]:
        """Validate synthetic data against official data sources.
        
        Args:
            synthetic_df: Generated synthetic data with VAT flags
            hmrc_target_bands: HMRC VAT-registered firm targets by turnover band
            ons_total_target: ONS total firm count target  
            ons_employment_df: ONS employment data for validation
            hmrc_sector_df: HMRC sector data for validation
            vat_liability_df: VAT liability data for validation
            
        Returns:
            Tuple of (hmrc_accuracy, ons_accuracy, employment_accuracy, sector_accuracy, vat_liability_accuracy)
        """
        logger.info("Validating synthetic data against official data sources...")
        
        # 1. HMRC VAT Firm Validation (VAT-registered firms only)
        def map_to_hmrc_band(turnover_k):
            if turnover_k <= 0:
                return 'Negative_or_Zero'
            elif turnover_k <= 85:
                return '£1_to_Threshold'
            elif turnover_k <= 150:
                return '£Threshold_to_£150k'
            elif turnover_k <= 300:
                return '£150k_to_£300k'
            elif turnover_k <= 500:
                return '£300k_to_£500k'
            elif turnover_k <= 1000:
                return '£500k_to_£1m'
            elif turnover_k <= 10000:
                return '£1m_to_£10m'
            else:
                return 'Greater_than_£10m'
        
        # Map all firms to HMRC bands for validation
        synthetic_df['hmrc_band'] = synthetic_df['annual_turnover_k'].apply(map_to_hmrc_band)
        all_bands = synthetic_df.groupby('hmrc_band')['weight'].sum().round().astype(int)
        
        # === VAT REGISTRATION VALIDATION ===
        vat_registered_count = synthetic_df[synthetic_df['vat_registered'] == True]['weight'].sum()
        hmrc_total_vat = sum(hmrc_target_bands.values())
        vat_accuracy = 1 - abs(vat_registered_count - hmrc_total_vat) / hmrc_total_vat
        
        self._print_validation_section("VAT REGISTRATION VALIDATION", 80)
        print(f"VAT Registered (weighted): {vat_registered_count:,.0f}")
        print(f"HMRC Total VAT firms:      {hmrc_total_vat:,}")
        print(f"Difference:                {vat_registered_count - hmrc_total_vat:+,.0f}")
        print(f"VAT Registration Accuracy: {vat_accuracy:.1%}")
        
        # === TURNOVER BAND VALIDATION ===
        self._print_validation_section("TURNOVER BAND VALIDATION", 80)
        print(f"{'Band':>25} {'Synthetic':>12} {'Target':>12} {'Source':>8} {'Accuracy':>10}")
        print("-" * 75)
        
        hmrc_band_accuracies = []
        
        # Validate each HMRC band
        for band_name, target_count in hmrc_target_bands.items():
            synthetic_count = all_bands.get(band_name, 0)
            accuracy = 1 - abs(synthetic_count - target_count) / target_count if target_count > 0 else (1.0 if synthetic_count == 0 else 0.0)
            
            # Special handling for £1_to_Threshold (ONS-based, not HMRC target)
            if band_name == '£1_to_Threshold':
                status = "○"
                source = "ONS-based"
            else:
                hmrc_band_accuracies.append(accuracy)
                status = "✓" if accuracy > 0.90 else "⚠" if accuracy > 0.80 else "✗"
                source = "HMRC"
            
            print(f"  {status} {band_name:>22}: {synthetic_count:>10,} vs {target_count:>10,} {source:>8} ({accuracy:>6.1%})")
        
        hmrc_accuracy = np.mean(hmrc_band_accuracies) if hmrc_band_accuracies else 0.0
        print("-" * 75)
        print(f"HMRC CALIBRATION ACCURACY: {hmrc_accuracy:.1%}")
        
        # === ONS POPULATION VALIDATION ===
        total_synthetic_weighted = synthetic_df['weight'].sum()
        ons_population_accuracy = 1 - abs(total_synthetic_weighted - ons_total_target) / ons_total_target
        
        self._print_validation_section("ONS POPULATION VALIDATION")
        print(f"Synthetic Total: {total_synthetic_weighted:,.0f}")
        print(f"ONS Target:      {ons_total_target:,}")
        print(f"Difference:      {total_synthetic_weighted - ons_total_target:+,.0f}")
        print(f"ONS Accuracy:    {ons_population_accuracy:.1%}")
        
        # === EMPLOYMENT BAND VALIDATION ===
        def _map_employment_to_band(employment: int) -> str:
            """Map employment count to ONS employment band."""
            if employment <= 4:
                return '0-4'
            elif employment <= 9:
                return '5-9'
            elif employment <= 19:
                return '10-19'
            elif employment <= 49:
                return '20-49'
            elif employment <= 99:
                return '50-99'
            elif employment <= 249:
                return '100-249'
            else:
                return '250+'
        
        employment_bands = ['0-4', '5-9', '10-19', '20-49', '50-99', '100-249', '250+']
        ons_employment_targets = {}
        
        # Get ONS employment targets
        for band in employment_bands:
            if band in ons_employment_df.columns:
                sector_rows = ons_employment_df[~ons_employment_df['Description'].str.contains('Total', na=False)]
                ons_employment_targets[band] = sector_rows[band].fillna(0).sum()
            else:
                ons_employment_targets[band] = 0
        
        # Calculate synthetic employment distribution
        synthetic_df['employment_band'] = synthetic_df['employment'].apply(_map_employment_to_band)
        synthetic_employment_counts = synthetic_df.groupby('employment_band')['weight'].sum().round().astype(int)
        
        self._print_validation_section("EMPLOYMENT BAND VALIDATION")
        print(f"{'Band':>8} {'Synthetic':>10} {'ONS Target':>11} {'Accuracy':>10}")
        print("-" * 65)
        
        employment_accuracies = []
        for band in employment_bands:
            ons_target = ons_employment_targets.get(band, 0)
            synthetic_count = synthetic_employment_counts.get(band, 0)
            accuracy = 1 - abs(synthetic_count - ons_target) / ons_target if ons_target > 0 else (1.0 if synthetic_count == 0 else 0.0)
            employment_accuracies.append(accuracy)
            
            status = "✓" if accuracy > 0.90 else "⚠" if accuracy > 0.80 else "✗"
            print(f"  {status} {band:>6}: {synthetic_count:>8,} vs {ons_target:>9,} ({accuracy:>6.1%})")
        
        print("-" * 65)
        employment_accuracy = self._print_accuracy_breakdown(employment_accuracies, len(employment_bands), "EMPLOYMENT")
        
        # === SECTOR VALIDATION (VAT-registered firms only) ===
        sector_rows = hmrc_sector_df[hmrc_sector_df['Trade_Sector'] != 'Total'].copy()
        
        # Calculate synthetic VAT-registered sector distribution
        synthetic_df['sic_numeric'] = synthetic_df['sic_code'].astype(int)
        vat_registered_firms = synthetic_df[synthetic_df['vat_registered'] == True]
        synthetic_vat_sector_counts = vat_registered_firms.groupby('sic_numeric')['weight'].sum().round().astype(int)
        
        self._print_validation_section("SECTOR VALIDATION (VAT-registered firms)")
        print(f"{'SIC':>5} {'Synthetic VAT':>12} {'HMRC Target':>12} {'Accuracy':>10}")
        print("-" * 65)
        
        sector_accuracies = []
        for _, sector_row in sector_rows.iterrows():
            sic_code = int(sector_row['Trade_Sector'])
            hmrc_target = sector_row['2023-24']
            
            synthetic_vat_count = synthetic_vat_sector_counts.get(sic_code, 0)
            accuracy = 1 - abs(synthetic_vat_count - hmrc_target) / hmrc_target if hmrc_target > 0 else (1.0 if synthetic_vat_count == 0 else 0.0)
            sector_accuracies.append(accuracy)
            
            status = "✓" if accuracy > 0.90 else "⚠" if accuracy > 0.80 else "✗"
            print(f"  {status} {sic_code:>3}: {synthetic_vat_count:>10,} vs {hmrc_target:>10,} ({accuracy:>6.1%})")
        
        print("-" * 65)
        sector_accuracy = self._print_accuracy_breakdown(sector_accuracies, len(sector_accuracies), "SECTOR")
        
        # === VAT LIABILITY VALIDATION ===
        # Get VAT liability sector data (excluding total)
        vat_liability_rows = vat_liability_df[vat_liability_df['Trade_Sector'] != 'Total'].copy()
        
        # Calculate synthetic VAT liability by sector
        synthetic_df['vat_liability_k'] = synthetic_df['annual_turnover_k'] - synthetic_df['annual_input_k']
        synthetic_df['sic_numeric'] = synthetic_df['sic_code'].astype(int)
        
        # Group by sector and calculate weighted VAT liability
        synthetic_vat_liability = synthetic_df.groupby('sic_numeric').apply(
            lambda x: (x['vat_liability_k'] * x['weight']).sum()
        ).reset_index(name='synthetic_vat_liability_k')
        
        self._print_validation_section("VAT LIABILITY VALIDATION (by sector)")
        print(f"{'SIC':>5} {'Synthetic (£m)':>14} {'Target (£m)':>12} {'Accuracy':>10}")
        print("-" * 65)
        
        vat_liability_accuracies = []
        for _, vat_row in vat_liability_rows.iterrows():
            sic_code = int(vat_row['Trade_Sector'])
            target_millions = vat_row['2023-24']  # in millions £
            target_k = target_millions * 1000  # convert to £k
            
            # Get synthetic VAT liability for this sector
            sector_data = synthetic_vat_liability[synthetic_vat_liability['sic_numeric'] == sic_code]
            if not sector_data.empty:
                synthetic_k = sector_data['synthetic_vat_liability_k'].iloc[0]
            else:
                synthetic_k = 0
            
            synthetic_millions = synthetic_k / 1000  # convert back to millions for display
            
            # Calculate accuracy (handle negative targets)
            if abs(target_millions) > 0.1:  # Skip near-zero targets
                # For negative targets, check if signs match and relative magnitude
                if target_millions < 0 and synthetic_millions < 0:
                    # Both negative - check relative difference
                    accuracy = 1 - min(abs(synthetic_millions - target_millions) / abs(target_millions), 1.0)
                elif target_millions > 0 and synthetic_millions > 0:
                    # Both positive - check relative difference
                    accuracy = 1 - min(abs(synthetic_millions - target_millions) / target_millions, 1.0)
                else:
                    # Sign mismatch - poor accuracy
                    accuracy = max(0, 1 - abs(synthetic_millions - target_millions) / max(abs(target_millions), 1))
            else:
                accuracy = 1.0 if abs(synthetic_millions) < 1 else 0.0
            
            vat_liability_accuracies.append(accuracy)
            
            status = "✓" if accuracy > 0.70 else "⚠" if accuracy > 0.50 else "✗"
            print(f"  {status} {sic_code:>3}: {synthetic_millions:>12.1f} vs {target_millions:>10.1f} ({accuracy:>6.1%})")
        
        print("-" * 65)
        vat_liability_sector_accuracy = self._print_accuracy_breakdown(vat_liability_accuracies, len(vat_liability_accuracies), "VAT LIABILITY BY SECTOR")
        
        # === VAT LIABILITY BY TURNOVER BAND VALIDATION ===
        # Get VAT liability by turnover band targets (excluding Negative_or_Zero)
        vat_liability_band_latest = vat_liability_band_df.iloc[-1]  # Get 2023-24 data
        vat_liability_band_targets = {
            '£1_to_Threshold': vat_liability_band_latest['£1_to_Threshold'],
            '£Threshold_to_£150k': vat_liability_band_latest['£Threshold_to_£150k'],
            '£150k_to_£300k': vat_liability_band_latest['£150k_to_£300k'],
            '£300k_to_£500k': vat_liability_band_latest['£300k_to_£500k'],
            '£500k_to_£1m': vat_liability_band_latest['£500k_to_£1m'],
            '£1m_to_£10m': vat_liability_band_latest['£1m_to_£10m'],
            'Greater_than_£10m': vat_liability_band_latest['Greater_than_£10m']
        }
        
        # Calculate synthetic VAT liability by turnover band (VAT-registered firms only)
        vat_registered_firms = synthetic_df[synthetic_df['vat_registered'] == True]
        synthetic_vat_band_liability = vat_registered_firms.groupby('hmrc_band').apply(
            lambda x: (x['vat_liability_k'] * x['weight']).sum()
        ).reset_index(name='synthetic_vat_liability_k')
        
        self._print_validation_section("VAT LIABILITY BY TURNOVER BAND VALIDATION")
        print(f"{'Band':>25} {'Synthetic (£m)':>14} {'Target (£m)':>12} {'Accuracy':>10}")
        print("-" * 75)
        
        vat_liability_band_accuracies = []
        for band_name, target_millions in vat_liability_band_targets.items():
            # Get synthetic VAT liability for this band
            band_data = synthetic_vat_band_liability[synthetic_vat_band_liability['hmrc_band'] == band_name]
            if not band_data.empty:
                synthetic_k = band_data['synthetic_vat_liability_k'].iloc[0]
            else:
                synthetic_k = 0
            
            synthetic_millions = synthetic_k / 1000  # convert back to millions for display
            
            # Calculate accuracy (handle negative targets)
            if abs(target_millions) > 0.1:  # Skip near-zero targets
                if target_millions < 0 and synthetic_millions < 0:
                    # Both negative - check relative difference
                    accuracy = 1 - min(abs(synthetic_millions - target_millions) / abs(target_millions), 1.0)
                elif target_millions > 0 and synthetic_millions > 0:
                    # Both positive - check relative difference
                    accuracy = 1 - min(abs(synthetic_millions - target_millions) / target_millions, 1.0)
                else:
                    # Sign mismatch - poor accuracy
                    accuracy = max(0, 1 - abs(synthetic_millions - target_millions) / max(abs(target_millions), 1))
            else:
                accuracy = 1.0 if abs(synthetic_millions) < 1 else 0.0
            
            vat_liability_band_accuracies.append(accuracy)
            
            status = "✓" if accuracy > 0.70 else "⚠" if accuracy > 0.50 else "✗"
            print(f"  {status} {band_name:>22}: {synthetic_millions:>12.1f} vs {target_millions:>10.1f} ({accuracy:>6.1%})")
        
        print("-" * 75)
        vat_liability_band_accuracy = self._print_accuracy_breakdown(vat_liability_band_accuracies, len(vat_liability_band_accuracies), "VAT LIABILITY BY BAND")
        
        # === FINAL SUMMARY ===
        overall_accuracy = (hmrc_accuracy + ons_population_accuracy + employment_accuracy + sector_accuracy + vat_liability_sector_accuracy + vat_liability_band_accuracy) / 6
        
        self._print_validation_section("CALIBRATION SUMMARY", 80)
        print(f"HMRC Turnover Bands:     {hmrc_accuracy:.1%}")
        print(f"ONS Population:          {ons_population_accuracy:.1%}")
        print(f"Employment Bands:        {employment_accuracy:.1%}")
        print(f"Sector Distribution:     {sector_accuracy:.1%}")
        print(f"VAT Liability by Sector: {vat_liability_sector_accuracy:.1%}")
        print(f"VAT Liability by Band:   {vat_liability_band_accuracy:.1%}")
        print(f"Overall Accuracy:        {overall_accuracy:.1%}")
        print(f"Total Population: {total_synthetic_weighted:,.0f} firms")
        
        return hmrc_accuracy, ons_population_accuracy, employment_accuracy, sector_accuracy, vat_liability_sector_accuracy, vat_liability_band_accuracy
    
    

    def generate_synthetic_firms(self) -> pd.DataFrame:
        """Main function to generate comprehensive synthetic firms population.
        
        Creates complete firm dataset with VAT registration flags, calibrated
        to match official ONS and HMRC data sources.
        
        Returns:
            DataFrame with synthetic firms data including VAT registration flags
        """
        logger.info("Starting synthetic firm generation...")
        
        # Load data
        ons_df, ons_employment_df, hmrc_turnover_df, hmrc_sector_df, vat_liability_df, vat_liability_band_df, ons_total = self.load_data()
        
        # Extract HMRC targets (VAT-registered firms only)
        hmrc_latest = hmrc_turnover_df.iloc[-1]
        hmrc_bands = {
            'Negative_or_Zero': hmrc_latest['Negative_or_Zero'],
            '£1_to_Threshold': hmrc_latest['£1_to_Threshold'],
            '£Threshold_to_£150k': hmrc_latest['£Threshold_to_£150k'],
            '£150k_to_£300k': hmrc_latest['£150k_to_£300k'],
            '£300k_to_£500k': hmrc_latest['£300k_to_£500k'],
            '£500k_to_£1m': hmrc_latest['£500k_to_£1m'],
            '£1m_to_£10m': hmrc_latest['£1m_to_£10m'],
            'Greater_than_£10m': hmrc_latest['Greater_than_£10m']
        }
        
        logger.info(f"Target populations:")
        logger.info(f"  ONS total firms: {ons_total:,} (includes all businesses)")
        logger.info(f"  HMRC VAT firms: {sum(hmrc_bands.values()):,} (VAT-registered only)")
        
        # Generate base firms from ONS structure
        base_sic_codes, base_turnover = self.generate_base_firms(ons_df)
        
        # Generate input values for firms
        base_input = self.generate_input_values(base_turnover, base_sic_codes)
        
        # Create target matrix for multi-objective optimization
        target_matrix, target_values = self.create_comprehensive_target_matrix(
            base_turnover, base_sic_codes, base_input, hmrc_bands, hmrc_sector_df, ons_employment_df, vat_liability_df, vat_liability_band_df, ons_total
        )
        
        # Optimize weights to match calibration targets
        optimized_weights = self.optimize_weights(target_matrix, target_values)
        
        # Apply final calibration (add zero firms manually)
        final_sic_codes, final_turnover, final_input, final_weights = self.apply_final_calibration(
            base_sic_codes, base_turnover, base_input, optimized_weights, hmrc_bands
        )
        
        # Assign employment to final firms
        employment_values = self.assign_employment(len(final_sic_codes), ons_employment_df)
        
        # Assign VAT registration flags
        vat_flags = self.assign_vat_registration_flags(final_turnover, hmrc_bands)
        
        # Convert to DataFrame
        logger.info("Converting to final DataFrame...")
        sic_codes_np = final_sic_codes.cpu().numpy().astype(int)
        turnover_np = final_turnover.cpu().numpy()
        input_np = final_input.cpu().numpy()
        vat_liability_np = turnover_np - input_np  # Calculate VAT liability
        
        synthetic_df = pd.DataFrame({
            'sic_code': [str(sic).zfill(5) for sic in sic_codes_np],
            'annual_turnover_k': turnover_np,
            'annual_input_k': input_np,
            'vat_liability_k': vat_liability_np,
            'employment': employment_values.cpu().numpy().astype(int),
            'weight': final_weights.cpu().numpy(),
            'vat_registered': vat_flags.cpu().numpy().astype(bool)
        })
        
        logger.info(f"Generated firm dataset:")
        logger.info(f"  Total firms: {len(synthetic_df):,}")
        logger.info(f"  Weighted population: {synthetic_df['weight'].sum():,.0f}")
        
        # Validation against all data sources
        self.validate_comprehensive_accuracy(synthetic_df, hmrc_bands, ons_total, ons_employment_df, hmrc_sector_df, vat_liability_df, vat_liability_band_df)
        
        return synthetic_df


def main():
    """Main execution function."""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger.info("UK BUSINESS POPULATION SYNTHETIC DATA GENERATION")
    logger.info("Generating synthetic firm records using PyTorch for efficient processing")
    
    # Initialize generator
    generator = SyntheticFirmGenerator(
        device="cpu"  # Use CPU for compatibility
    )
    
    # Generate synthetic data
    synthetic_df = generator.generate_synthetic_firms()
    
    # Save results
    output_path = Path(__file__).parent / 'synthetic_firms_turnover.csv'
    synthetic_df.to_csv(output_path, index=False)
    
    file_size_mb = output_path.stat().st_size / 1024 / 1024
    logger.info(f"Saved {len(synthetic_df):,} firms to {output_path}")
    logger.info(f"File size: {file_size_mb:.1f} MB")
    logger.info(f"Columns: {list(synthetic_df.columns)}")
    
    logger.info("Synthetic data generation complete!")


if __name__ == "__main__":
    main()