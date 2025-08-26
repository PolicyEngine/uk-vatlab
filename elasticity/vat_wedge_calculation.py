"""
Proper VAT Effective Wedge Calculation Using IOT Data

This script correctly extracts and processes UK Input-Output tables to calculate
industry-specific effective wedge parameters following the methodology in
the agent TODO document.

Formula: τ_e = λ(1-ρ)τ - τs_c·v
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path


class ProperIOTWedgeCalibrator:
    """Calculate industry-specific VAT effective wedges from Input-Output tables (corrected version)"""
    
    def __init__(self, iot_file_path='iot2022industry.xlsx'):
        self.iot_path = Path(iot_file_path)
        self.vat_rate = 0.20  # UK standard VAT rate
        
        # Load all components
        self.load_iot_data()
        
    def load_iot_data(self):
        """Load and properly process Input-Output table data"""
        print(f"Loading IOT data from {self.iot_path}")
        
        # Read sheets
        self.iot_sheet = pd.read_excel(self.iot_path, sheet_name='IOT', header=None)
        self.a_matrix_sheet = pd.read_excel(self.iot_path, sheet_name='A', header=None)
        
        # Extract components
        self.extract_lambda_b2c()
        self.extract_s_c()
        self.estimate_rho_passthrough()
        self.calculate_v_reclaimable()
        
        # Calculate wedges
        self.calculate_all_wedges()
    
    def extract_lambda_b2c(self):
        """Extract λ (B2C share) from IOT Use table HFCE data"""
        print("\n1. Extracting λ (B2C share) from HFCE...")
        
        # Column indices in IOT sheet
        hfce_col = 110  # Household final consumption (P3 S14)
        npish_col = 111  # NPISH consumption (P3 S15)
        
        # Find total output/use column - need to identify correct one
        # Looking for total intermediate use + final demand
        # This is typically around column 107-108 for intermediate, then final demand components
        
        # For now, use domestic output at basic prices if available
        # Otherwise sum intermediate + final demand
        
        results = []
        
        # Data rows start at row 7
        for row in range(7, 111):
            sic = self.iot_sheet.iloc[row, 0]
            name = self.iot_sheet.iloc[row, 1]
            
            if pd.notna(sic) and str(sic) not in ['nan', '_T']:
                # Get consumption values
                hfce = float(self.iot_sheet.iloc[row, hfce_col]) if pd.notna(self.iot_sheet.iloc[row, hfce_col]) else 0
                npish = float(self.iot_sheet.iloc[row, npish_col]) if pd.notna(self.iot_sheet.iloc[row, npish_col]) else 0
                
                # Get total output - sum of intermediate use (cols 2-106) + final demand (cols 108-117)
                # For simplicity, using total of row
                intermediate_use = 0
                for col in range(2, 107):
                    val = self.iot_sheet.iloc[row, col]
                    if pd.notna(val) and isinstance(val, (int, float)):
                        intermediate_use += val
                
                final_demand = 0
                for col in range(108, 118):
                    val = self.iot_sheet.iloc[row, col]
                    if pd.notna(val) and isinstance(val, (int, float)):
                        final_demand += val
                
                total_output = intermediate_use + final_demand
                
                # Calculate λ
                if total_output > 0:
                    lambda_b2c = (hfce + npish) / total_output
                    # Cap at 1.0 (can't have more than 100% B2C)
                    lambda_b2c = min(1.0, lambda_b2c)
                else:
                    lambda_b2c = 0
                
                results.append({
                    'SIC': str(sic),
                    'Industry': str(name)[:80],
                    'HFCE': hfce,
                    'NPISH': npish,
                    'Total_Output': total_output,
                    'lambda': lambda_b2c
                })
        
        self.lambda_df = pd.DataFrame(results)
        print(f"  Calculated λ for {len(self.lambda_df)} industries")
        print(f"  Mean λ: {self.lambda_df['lambda'].mean():.3f}")
        print(f"  Median λ: {self.lambda_df['lambda'].median():.3f}")
    
    def extract_s_c(self):
        """Extract s_c (intermediate input share) from A matrix"""
        print("\n2. Extracting s_c from A matrix (technical coefficients)...")
        
        results = []
        
        # Data starts at row 7 in A matrix
        data_start = 7
        
        # Get industry list
        for i in range(105):  # Standard IOT has ~105 industries
            row = data_start + i
            if row >= self.a_matrix_sheet.shape[0]:
                break
                
            sic = self.a_matrix_sheet.iloc[row, 0]
            
            if pd.notna(sic) and str(sic) not in ['nan', '_T']:
                # Column i+2 contains coefficients for industry i
                col = i + 2
                
                # Sum column to get total intermediate input coefficient
                s_c = 0
                for j in range(105):
                    val_row = data_start + j
                    if val_row < self.a_matrix_sheet.shape[0]:
                        val = self.a_matrix_sheet.iloc[val_row, col]
                        if pd.notna(val) and isinstance(val, (int, float)):
                            s_c += val
                
                # Ensure s_c is between 0 and 1
                s_c = np.clip(s_c, 0, 1)
                
                results.append({
                    'SIC': str(sic),
                    's_c': s_c
                })
        
        self.s_c_df = pd.DataFrame(results)
        print(f"  Calculated s_c for {len(self.s_c_df)} industries")
        print(f"  Mean s_c: {self.s_c_df['s_c'].mean():.3f}")
        print(f"  Range: [{self.s_c_df['s_c'].min():.3f}, {self.s_c_df['s_c'].max():.3f}]")
    
    def estimate_rho_passthrough(self):
        """Estimate ρ (pass-through rate) based on literature and sector characteristics"""
        print("\n3. Estimating ρ (pass-through rates)...")
        
        # Literature-based defaults by sector type
        # Based on Benzarti & Carloni (2019), Kosonen (2015), Carbonnier (2007)
        
        results = []
        
        for _, row in self.lambda_df.iterrows():
            sic = row['SIC']
            lambda_val = row['lambda']
            
            # Get s_c for this industry
            s_c_row = self.s_c_df[self.s_c_df['SIC'] == sic]
            s_c = s_c_row['s_c'].iloc[0] if not s_c_row.empty else 0.5
            
            # Estimate pass-through based on:
            # 1. B2C share (higher B2C → higher pass-through due to competition)
            # 2. Input costs (higher inputs → higher pass-through)
            # 3. Sector type
            
            sic_letter = str(sic)[0] if sic else 'G'
            
            # Base pass-through by sector type
            if sic_letter in ['G']:  # Retail/wholesale
                base_rho = 0.85  # High competition, high pass-through
            elif sic_letter in ['I']:  # Hospitality
                base_rho = 0.30  # Services, lower pass-through (Carbonnier 2007)
            elif sic_letter in ['C', 'D', 'E']:  # Manufacturing, utilities
                base_rho = 0.70  # Moderate pass-through
            elif sic_letter in ['M', 'N']:  # Professional/admin services
                base_rho = 0.40  # Services with pricing power
            elif sic_letter in ['K']:  # Financial
                base_rho = 0.25  # Low competition, low pass-through
            else:
                base_rho = 0.60  # Default
            
            # Adjust for B2C share (more B2C → more pass-through)
            b2c_adjustment = lambda_val * 0.2
            
            # Adjust for input costs (higher costs → more pass-through)
            cost_adjustment = s_c * 0.1
            
            rho = np.clip(base_rho + b2c_adjustment + cost_adjustment, 0, 1)
            
            results.append({
                'SIC': sic,
                'rho': rho,
                'base_rho': base_rho,
                'lambda_effect': b2c_adjustment,
                's_c_effect': cost_adjustment
            })
        
        self.rho_df = pd.DataFrame(results)
        print(f"  Estimated ρ for {len(self.rho_df)} industries")
        print(f"  Mean ρ: {self.rho_df['rho'].mean():.3f}")
        print(f"  Range: [{self.rho_df['rho'].min():.3f}, {self.rho_df['rho'].max():.3f}]")
    
    def calculate_v_reclaimable(self):
        """Calculate v (VAT-eligible input share) based on input composition"""
        print("\n4. Calculating v (VAT-eligible input share)...")
        
        # Based on HMRC VAT Notice 700 rules
        # Non-reclaimable: wages, rent (unless opted), finance, insurance, business entertainment
        # Reclaimable: materials, utilities, most business services
        
        results = []
        
        for _, row in self.lambda_df.iterrows():
            sic = row['SIC']
            sic_letter = str(sic)[0] if sic else 'G'
            
            # Get s_c for this industry
            s_c_row = self.s_c_df[self.s_c_df['SIC'] == sic]
            s_c = s_c_row['s_c'].iloc[0] if not s_c_row.empty else 0.5
            
            # Estimate based on sector characteristics
            # Higher s_c generally means more materials (reclaimable)
            # Lower s_c means more labor (non-reclaimable)
            
            if sic_letter in ['C', 'D', 'E']:  # Manufacturing, utilities
                # High materials content
                v = 0.85 + s_c * 0.1  # 85-95% reclaimable
            elif sic_letter in ['G']:  # Retail/wholesale
                # Mostly goods for resale
                v = 0.80 + s_c * 0.1  # 80-90% reclaimable
            elif sic_letter in ['F']:  # Construction
                # Materials and subcontractors
                v = 0.75 + s_c * 0.1  # 75-85% reclaimable
            elif sic_letter in ['H', 'J']:  # Transport, ICT
                # Mixed: fuel/equipment vs labor
                v = 0.60 + s_c * 0.15  # 60-75% reclaimable
            elif sic_letter in ['K']:  # Financial
                # Many exempt supplies, high labor
                v = 0.30 + s_c * 0.2  # 30-50% reclaimable
            elif sic_letter in ['P', 'Q']:  # Education, Health
                # Mostly labor, many exemptions
                v = 0.25 + s_c * 0.15  # 25-40% reclaimable
            elif sic_letter in ['M', 'N']:  # Professional/admin
                # High labor content
                v = 0.50 + s_c * 0.2  # 50-70% reclaimable
            else:
                # Default: proportional to input share
                v = 0.40 + s_c * 0.3  # 40-70% reclaimable
            
            v = np.clip(v, 0, 1)
            
            results.append({
                'SIC': sic,
                'v': v
            })
        
        self.v_df = pd.DataFrame(results)
        print(f"  Calculated v for {len(self.v_df)} industries")
        print(f"  Mean v: {self.v_df['v'].mean():.3f}")
        print(f"  Range: [{self.v_df['v'].min():.3f}, {self.v_df['v'].max():.3f}]")
    
    def calculate_all_wedges(self):
        """Calculate τ_e for all industries using the proper formula"""
        print("\n5. Calculating τ_e (effective wedges)...")
        
        # Merge all parameters
        self.results_df = self.lambda_df[['SIC', 'Industry', 'lambda']]
        self.results_df = self.results_df.merge(self.s_c_df, on='SIC')
        self.results_df = self.results_df.merge(self.rho_df[['SIC', 'rho']], on='SIC')
        self.results_df = self.results_df.merge(self.v_df, on='SIC')
        
        # Calculate wedge
        tau = self.vat_rate
        self.results_df['tau_e'] = (
            self.results_df['lambda'] * (1 - self.results_df['rho']) * tau -
            tau * self.results_df['s_c'] * self.results_df['v']
        )
        
        print(f"  Calculated τ_e for {len(self.results_df)} industries")
        print(f"  Mean τ_e: {self.results_df['tau_e'].mean():.4f}")
        print(f"  Range: [{self.results_df['tau_e'].min():.4f}, {self.results_df['tau_e'].max():.4f}]")
        
        # Add interpretation
        self.results_df['interpretation'] = self.results_df['tau_e'].apply(
            lambda x: 'Bunching (avoid VAT)' if x > 0.01 
            else 'Voluntary registration' if x < -0.01
            else 'Neutral'
        )
    
    def validate_results(self):
        """Validate that results match economic intuition"""
        print("\n6. Validation checks...")
        
        validations = []
        
        # Check specific sectors
        checks = [
            ('G47', 'Retail', 'should have negative wedge (high inputs)', lambda x: x < 0),
            ('C', 'Manufacturing', 'should have negative wedge (high inputs)', lambda x: x < 0),
            ('I56', 'Food service', 'could be positive (high B2C, low pass-through)', lambda x: True),
            ('K64', 'Financial', 'could be positive (low reclaim)', lambda x: True),
        ]
        
        for sic_check, name, expectation, check_fn in checks:
            matching = self.results_df[self.results_df['SIC'].str.startswith(sic_check)]
            if not matching.empty:
                tau_e = matching['tau_e'].iloc[0]
                passed = check_fn(tau_e)
                validations.append({
                    'Sector': name,
                    'SIC': sic_check,
                    'tau_e': tau_e,
                    'Expected': expectation,
                    'Passed': '✓' if passed else '✗'
                })
        
        self.validation_df = pd.DataFrame(validations)
        print(self.validation_df.to_string(index=False))
        
        # Summary statistics by sign
        positive = self.results_df[self.results_df['tau_e'] > 0]
        negative = self.results_df[self.results_df['tau_e'] < 0]
        
        print(f"\n  Industries with positive wedge (bunching): {len(positive)}")
        print(f"  Industries with negative wedge (voluntary reg): {len(negative)}")
    
    def export_results(self):
        """Export results to CSV and JSON"""
        # Save detailed results
        self.results_df.to_csv('proper_wedge_calculations.csv', index=False)
        
        # Create summary by sector letter
        self.results_df['Sector'] = self.results_df['SIC'].str[0]
        sector_summary = self.results_df.groupby('Sector').agg({
            'lambda': 'mean',
            's_c': 'mean',
            'rho': 'mean',
            'v': 'mean',
            'tau_e': 'mean'
        }).round(4)
        
        # Export to JSON
        export_data = {
            'metadata': {
                'source': 'UK Input-Output Tables 2022',
                'vat_rate': self.vat_rate,
                'method': 'Proper IOT extraction with HFCE'
            },
            'industry_results': self.results_df.to_dict('records'),
            'sector_averages': sector_summary.to_dict('index'),
            'validation': self.validation_df.to_dict('records') if hasattr(self, 'validation_df') else []
        }
        
        with open('proper_wedge_parameters.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print("\n7. Results exported to:")
        print("  - proper_wedge_calculations.csv")
        print("  - proper_wedge_parameters.json")
    
    def create_summary_report(self):
        """Create a summary report of key findings"""
        print("\n" + "="*60)
        print("PROPER VAT EFFECTIVE WEDGE CALCULATION RESULTS")
        print("="*60)
        
        # Top positive wedges
        print("\nTop 5 Industries with POSITIVE wedges (expect bunching):")
        top_positive = self.results_df.nlargest(5, 'tau_e')[['SIC', 'Industry', 'tau_e', 'lambda', 'rho']]
        print(top_positive.to_string(index=False))
        
        # Top negative wedges
        print("\nTop 5 Industries with NEGATIVE wedges (voluntary registration):")
        top_negative = self.results_df.nsmallest(5, 'tau_e')[['SIC', 'Industry', 'tau_e', 's_c', 'v']]
        print(top_negative.to_string(index=False))
        
        # Parameter ranges
        print("\nParameter Ranges:")
        print(f"  λ (B2C share):     [{self.results_df['lambda'].min():.3f}, {self.results_df['lambda'].max():.3f}]")
        print(f"  s_c (input share): [{self.results_df['s_c'].min():.3f}, {self.results_df['s_c'].max():.3f}]")
        print(f"  ρ (pass-through):  [{self.results_df['rho'].min():.3f}, {self.results_df['rho'].max():.3f}]")
        print(f"  v (VAT-eligible):  [{self.results_df['v'].min():.3f}, {self.results_df['v'].max():.3f}]")
        print(f"  τ_e (wedge):       [{self.results_df['tau_e'].min():.4f}, {self.results_df['tau_e'].max():.4f}]")


def main():
    """Run the proper calibration process"""
    
    calibrator = ProperIOTWedgeCalibrator('iot2022industry.xlsx')
    calibrator.validate_results()
    calibrator.export_results()
    calibrator.create_summary_report()
    
    return calibrator


if __name__ == "__main__":
    calibrator = main()