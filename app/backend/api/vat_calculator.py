import pandas as pd
import numpy as np
import time
import logging
from typing import Dict, List
from models import PolicyReform, TaperType

logger = logging.getLogger(__name__)


class VATCalculator:
    def __init__(self, data_path: str = None):
        start_time = time.time()
        if data_path is None:
            # Try different possible paths
            import os
            possible_paths = [
                "/app/data/synthetic_firms.csv",  # Docker path
                "./data/synthetic_firms.csv",     # Vercel path
                "../../analysis/synthetic_firms.csv",  # Relative path from backend
                "/Users/nikhilwoodruff/policyengine/uk-vatlab/analysis/synthetic_firms.csv"  # Absolute path
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    data_path = path
                    break
            if data_path is None:
                raise FileNotFoundError("Could not find synthetic_firms.csv")
        
        logger.info(f"Loading data from {data_path}")
        self.firms_df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(self.firms_df)} firms in {time.time() - start_time:.3f}s")
        
        # SIC code descriptions mapping
        self.sic_descriptions = {
            1: "Crop and animal production",
            2: "Forestry and logging",
            3: "Fishing and aquaculture",
            5: "Mining of coal and lignite",
            6: "Extraction of crude petroleum and natural gas",
            7: "Mining of metal ores",
            8: "Other mining and quarrying",
            9: "Mining support service activities",
            10: "Manufacture of food products",
            11: "Manufacture of beverages",
            12: "Manufacture of tobacco products",
            13: "Manufacture of textiles",
            14: "Manufacture of wearing apparel",
            15: "Manufacture of leather and related products",
            16: "Manufacture of wood and cork products",
            17: "Manufacture of paper and paper products",
            18: "Printing and reproduction of recorded media",
            19: "Manufacture of coke and refined petroleum products",
            20: "Manufacture of chemicals and chemical products",
            21: "Manufacture of pharmaceutical products",
            22: "Manufacture of rubber and plastic products",
            23: "Manufacture of other non-metallic mineral products",
            24: "Manufacture of basic metals",
            25: "Manufacture of fabricated metal products",
            26: "Manufacture of computer and electronic products",
            27: "Manufacture of electrical equipment",
            28: "Manufacture of machinery and equipment",
            29: "Manufacture of motor vehicles",
            30: "Manufacture of other transport equipment",
            31: "Manufacture of furniture",
            32: "Other manufacturing",
            33: "Repair and installation of machinery",
            35: "Electricity, gas, steam and air supply",
            36: "Water collection, treatment and supply",
            37: "Sewerage",
            38: "Waste collection and disposal",
            39: "Remediation activities",
            41: "Construction of buildings",
            42: "Civil engineering",
            43: "Specialised construction activities",
            45: "Wholesale and retail trade of motor vehicles",
            46: "Wholesale trade",
            47: "Retail trade",
            49: "Land transport",
            50: "Water transport",
            51: "Air transport",
            52: "Warehousing and transport support",
            53: "Postal and courier activities",
            55: "Accommodation",
            56: "Food and beverage service activities",
            58: "Publishing activities",
            59: "Motion picture and TV production",
            60: "Programming and broadcasting",
            61: "Telecommunications",
            62: "Computer programming and consultancy",
            63: "Information service activities",
            64: "Financial service activities",
            65: "Insurance and pension funding",
            66: "Auxiliary financial services",
            68: "Real estate activities",
            69: "Legal and accounting activities",
            70: "Head offices and management consultancy",
            71: "Architectural and engineering activities",
            72: "Scientific research and development",
            73: "Advertising and market research",
            74: "Other professional activities",
            75: "Veterinary activities",
            77: "Rental and leasing activities",
            78: "Employment activities",
            79: "Travel agency and tour operator activities",
            80: "Security and investigation activities",
            81: "Services to buildings and landscape",
            82: "Office administrative and support activities",
            84: "Public administration and defence",
            85: "Education",
            86: "Human health activities",
            87: "Residential care activities",
            88: "Social work activities",
            90: "Creative, arts and entertainment",
            91: "Libraries, archives and museums",
            92: "Gambling and betting activities",
            93: "Sports and recreation activities",
            94: "Activities of membership organisations",
            95: "Repair of computers and household goods",
            96: "Other personal service activities"
        }
        self.fiscal_years = [
            {"year": "2025-26", "baseline": 90000, "firm_growth": 1.0516},
            {"year": "2026-27", "baseline": 90000, "firm_growth": 1.0779},
            {"year": "2027-28", "baseline": 90000, "firm_growth": 1.1102},
            {"year": "2028-29", "baseline": 90000, "firm_growth": 1.1424},
            {"year": "2029-30", "baseline": 90000, "firm_growth": 1.1761},
            {"year": "2030-31", "baseline": 90000, "firm_growth": 1.2114},
        ]
        self.vat_rate = 0.20
        # Create 10k-wide revenue bands up to 200k, then larger bands
        self.revenue_bands = []
        for i in range(0, 200000, 10000):
            self.revenue_bands.append((i, i + 10000, f"£{i//1000}k-{(i+10000)//1000}k"))
        # Add larger bands for higher revenues
        self.revenue_bands.extend([
            (200000, 300000, "£200k-300k"),
            (300000, 500000, "£300k-500k"),
            (500000, 1000000, "£500k-1m"),
            (1000000, float('inf'), "£1m+"),
        ])

    def calculate_effective_vat_rate(self, turnover_pounds: float, reform: PolicyReform) -> float:
        """Calculate effective VAT rate based on turnover and taper settings."""
        if turnover_pounds < reform.registration_threshold:
            return 0.0
        
        if reform.taper_type == TaperType.NONE:
            return self.vat_rate
        
        taper_start = reform.taper_start or reform.registration_threshold * 0.75
        taper_end = reform.taper_end or reform.registration_threshold
        
        if reform.taper_type == TaperType.MODERATE:
            taper_start = max(65000, reform.registration_threshold - 25000)
            taper_end = reform.registration_threshold + 20000
        elif reform.taper_type == TaperType.AGGRESSIVE:
            taper_start = max(50000, reform.registration_threshold - 35000)
            taper_end = reform.registration_threshold + 10000
        
        if turnover_pounds <= taper_start:
            return 0.0
        elif turnover_pounds >= taper_end:
            return self.vat_rate
        else:
            progress = (turnover_pounds - taper_start) / (taper_end - taper_start)
            return self.vat_rate * progress

    def age_data(self, year_index: int) -> pd.DataFrame:
        """Apply growth factors to age the data to a specific year."""
        df = self.firms_df.copy()
        growth_factor = self.fiscal_years[year_index]["firm_growth"]
        
        df['weight'] = df['weight'] * growth_factor
        df['annual_turnover_k'] = df['annual_turnover_k'] * (1 + (year_index * 0.025))
        
        return df

    def calculate_vat_liability(self, df: pd.DataFrame, threshold: int, reform: PolicyReform = None) -> pd.DataFrame:
        """Apply VAT threshold to existing VAT liability data."""
        start_time = time.time()
        df = df.copy()
        logger.info(f"Starting VAT liability calculation for {len(df)} firms")
        
        # Convert turnover to pounds for threshold comparison
        df['turnover_pounds'] = df['annual_turnover_k'] * 1000
        # Convert existing VAT liability from thousands to pounds
        df['vat_liability_base'] = df['vat_liability_k'] * 1000
        logger.info(f"Converted values to pounds: {time.time() - start_time:.3f}s")
        
        if reform and reform.taper_type != TaperType.NONE:
            # Vectorized calculation of taper multiplier
            taper_start = reform.taper_start or reform.registration_threshold * 0.75
            taper_end = reform.taper_end or reform.registration_threshold
            
            if reform.taper_type == TaperType.MODERATE:
                taper_start = max(65000, reform.registration_threshold - 25000)
                taper_end = reform.registration_threshold + 20000
            elif reform.taper_type == TaperType.AGGRESSIVE:
                taper_start = max(50000, reform.registration_threshold - 35000)
                taper_end = reform.registration_threshold + 10000
            
            # Calculate taper multiplier (0 to 1)
            df['taper_multiplier'] = 0.0
            
            # Firms below threshold get 0 multiplier (no VAT)
            # Firms in taper range get proportional multiplier
            in_taper = (df['turnover_pounds'] >= taper_start) & (df['turnover_pounds'] < taper_end)
            progress = (df.loc[in_taper, 'turnover_pounds'] - taper_start) / (taper_end - taper_start)
            df.loc[in_taper, 'taper_multiplier'] = progress
            
            # Firms above taper end get full multiplier
            above_taper = df['turnover_pounds'] >= taper_end
            df.loc[above_taper, 'taper_multiplier'] = 1.0
            
            # Apply taper to existing VAT liability
            df['vat_liability'] = df['vat_liability_base'] * df['taper_multiplier']
            logger.info(f"Applied VAT taper: {time.time() - start_time:.3f}s")
        else:
            # Simple threshold: firms below threshold pay no VAT
            df['is_registered'] = df['turnover_pounds'] >= threshold
            df['vat_liability'] = np.where(
                df['is_registered'],
                df['vat_liability_base'],
                0
            )
            logger.info(f"Applied VAT threshold: {time.time() - start_time:.3f}s")
        
        logger.info(f"VAT liability calculation complete: {time.time() - start_time:.3f}s")
        return df

    def calculate_yearly_impact(self, year_index: int, reform: PolicyReform, return_dataframes: bool = False) -> Dict:
        """Calculate impact for a specific year."""
        start_time = time.time()
        year_info = self.fiscal_years[year_index]
        df = self.age_data(year_index)
        logger.info(f"Year {year_info['year']}: Aged data in {time.time() - start_time:.3f}s")
        
        baseline_start = time.time()
        baseline_df = self.calculate_vat_liability(df.copy(), year_info["baseline"])
        logger.info(f"Year {year_info['year']}: Baseline VAT in {time.time() - baseline_start:.3f}s")
        
        reform_start = time.time()
        reform_df = self.calculate_vat_liability(df.copy(), reform.registration_threshold, reform)
        logger.info(f"Year {year_info['year']}: Reform VAT in {time.time() - reform_start:.3f}s")
        
        baseline_revenue = (baseline_df['vat_liability'] * baseline_df['weight']).sum()
        reform_revenue = (reform_df['vat_liability'] * reform_df['weight']).sum()
        
        baseline_registered = baseline_df[baseline_df['vat_liability'] > 0]['weight'].sum()
        reform_registered = reform_df[reform_df['vat_liability'] > 0]['weight'].sum()
        
        result = {
            "year": year_info["year"],
            "baseline_revenue": baseline_revenue / 1e9,
            "reform_revenue": reform_revenue / 1e9,
            "revenue_impact": (reform_revenue - baseline_revenue) / 1e6,
            "firms_affected": int(abs(reform_registered - baseline_registered)),
            "newly_registered": int(max(0, reform_registered - baseline_registered)),
            "newly_deregistered": int(max(0, baseline_registered - reform_registered))
        }
        
        if return_dataframes:
            result["baseline_df"] = baseline_df
            result["reform_df"] = reform_df
            
        return result

    def calculate_sector_impacts(self, reform: PolicyReform, yearly_results: List[Dict] = None) -> List[Dict]:
        """Calculate impacts by sector across all years."""
        start_time = time.time()
        sector_impacts = {}
        logger.info(f"Starting sector impact calculation")
        
        # If yearly results not provided, calculate them with dataframes
        if yearly_results is None:
            yearly_results = [
                self.calculate_yearly_impact(i, reform, return_dataframes=True) 
                for i in range(len(self.fiscal_years))
            ]
        
        for year_result in yearly_results:
            if 'baseline_df' not in year_result:
                # Need to recalculate with dataframes
                year_index = self.fiscal_years.index(
                    next(y for y in self.fiscal_years if y["year"] == year_result["year"])
                )
                year_result = self.calculate_yearly_impact(year_index, reform, return_dataframes=True)
            
            baseline_df = year_result['baseline_df']
            reform_df = year_result['reform_df']
            
            for sector in baseline_df['sic_code'].unique():
                if sector not in sector_impacts:
                    sector_impacts[sector] = {
                        "baseline_revenue": 0,
                        "reform_revenue": 0,
                        "firms_affected": set()
                    }
                
                sector_mask = baseline_df['sic_code'] == sector
                sector_baseline = (baseline_df[sector_mask]['vat_liability'] * 
                                 baseline_df[sector_mask]['weight']).sum()
                sector_reform = (reform_df[sector_mask]['vat_liability'] * 
                               reform_df[sector_mask]['weight']).sum()
                
                sector_impacts[sector]["baseline_revenue"] += sector_baseline
                sector_impacts[sector]["reform_revenue"] += sector_reform
                
                affected = baseline_df[sector_mask]['vat_liability'] != reform_df[sector_mask]['vat_liability']
                sector_impacts[sector]["firms_affected"].update(
                    baseline_df[sector_mask & affected].index.tolist()
                )
        
        logger.info(f"Sector impacts calculated in {time.time() - start_time:.3f}s")
        
        result = []
        for sector, data in sector_impacts.items():
            # Get sector description or use code as fallback
            sector_int = int(sector) if isinstance(sector, (np.integer, int)) else sector
            sector_name = self.sic_descriptions.get(sector_int, f"SIC {sector_int}")
            
            result.append({
                "sector": sector_name,
                "baseline_revenue": float(data["baseline_revenue"] / 1e9),
                "reform_revenue": float(data["reform_revenue"] / 1e9),
                "revenue_impact": float((data["reform_revenue"] - data["baseline_revenue"]) / 1e6),
                "firms_affected": int(len(data["firms_affected"]))
            })
        return result

    def calculate_revenue_band_impacts(self, reform: PolicyReform, yearly_results: List[Dict] = None) -> List[Dict]:
        """Calculate impacts by revenue band."""
        start_time = time.time()
        band_impacts = []
        logger.info(f"Starting revenue band impact calculation")
        
        # If yearly results not provided, calculate them with dataframes
        if yearly_results is None:
            yearly_results = [
                self.calculate_yearly_impact(i, reform, return_dataframes=True) 
                for i in range(len(self.fiscal_years))
            ]
        
        for min_rev, max_rev, band_label in self.revenue_bands:
            band_data = {
                "band": band_label,
                "min_revenue": min_rev,
                "max_revenue": max_rev if max_rev != float('inf') else 999999999,
                "baseline_vat": 0,
                "reform_vat": 0,
                "firms_affected": 0
            }
            
            for year_result in yearly_results:
                if 'baseline_df' not in year_result:
                    # Need to recalculate with dataframes
                    year_index = self.fiscal_years.index(
                        next(y for y in self.fiscal_years if y["year"] == year_result["year"])
                    )
                    year_result = self.calculate_yearly_impact(year_index, reform, return_dataframes=True)
                
                baseline_df = year_result['baseline_df']
                reform_df = year_result['reform_df']
                
                band_mask = (baseline_df['turnover_pounds'] >= min_rev) & (baseline_df['turnover_pounds'] < max_rev)
                
                band_data["baseline_vat"] += (baseline_df[band_mask]['vat_liability'] * baseline_df[band_mask]['weight']).sum()
                band_data["reform_vat"] += (reform_df[band_mask]['vat_liability'] * reform_df[band_mask]['weight']).sum()
                
                affected = baseline_df[band_mask]['vat_liability'] != reform_df[band_mask]['vat_liability']
                band_data["firms_affected"] += affected.sum()
            
            band_data["baseline_vat"] /= 1e9
            band_data["reform_vat"] /= 1e9
            band_data["revenue_impact"] = (band_data["reform_vat"] - band_data["baseline_vat"]) * 1000
            
            band_impacts.append(band_data)
        
        logger.info(f"Revenue band impacts calculated in {time.time() - start_time:.3f}s")
        return band_impacts

    def analyze_reform(self, reform: PolicyReform) -> Dict:
        """Complete analysis of a VAT reform."""
        start_time = time.time()
        logger.info(f"Starting reform analysis for threshold={reform.registration_threshold}, taper={reform.taper_type}")
        
        # Initialize aggregators
        yearly_impacts = []
        all_baseline_dfs = []
        all_reform_dfs = []
        
        # Calculate yearly impacts and collect dataframes
        for year_index in range(len(self.fiscal_years)):
            year_info = self.fiscal_years[year_index]
            
            # Age data once per year
            df = self.age_data(year_index)
            
            # Calculate VAT liability once per year
            calc_start = time.time()
            baseline_df = self.calculate_vat_liability(df.copy(), year_info["baseline"])
            reform_df = self.calculate_vat_liability(df.copy(), reform.registration_threshold, reform)
            logger.info(f"Year {year_info['year']}: Calculated baseline and reform in {time.time() - calc_start:.3f}s")
            
            # Add year column for later aggregation
            baseline_df['year'] = year_info["year"]
            reform_df['year'] = year_info["year"]
            
            all_baseline_dfs.append(baseline_df)
            all_reform_dfs.append(reform_df)
            
            # Calculate yearly impact
            baseline_revenue = (baseline_df['vat_liability'] * baseline_df['weight']).sum()
            reform_revenue = (reform_df['vat_liability'] * reform_df['weight']).sum()
            baseline_registered = baseline_df[baseline_df['vat_liability'] > 0]['weight'].sum()
            reform_registered = reform_df[reform_df['vat_liability'] > 0]['weight'].sum()
            
            yearly_impacts.append({
                "year": year_info["year"],
                "baseline_revenue": baseline_revenue / 1e9,
                "reform_revenue": reform_revenue / 1e9,
                "revenue_impact": (reform_revenue - baseline_revenue) / 1e6,
                "firms_affected": int(abs(reform_registered - baseline_registered)),
                "newly_registered": int(max(0, reform_registered - baseline_registered)),
                "newly_deregistered": int(max(0, baseline_registered - reform_registered))
            })
        
        # Combine all years for band analysis
        all_baseline = pd.concat(all_baseline_dfs, ignore_index=True)
        all_reform = pd.concat(all_reform_dfs, ignore_index=True)
        
        # Create revenue band column using pd.cut for efficient binning
        band_edges = [band[0] for band in self.revenue_bands] + [self.revenue_bands[-1][1]]
        band_labels = [band[2] for band in self.revenue_bands]
        
        all_baseline['revenue_band'] = pd.cut(
            all_baseline['turnover_pounds'], 
            bins=band_edges, 
            labels=band_labels,
            include_lowest=True
        )
        all_reform['revenue_band'] = pd.cut(
            all_reform['turnover_pounds'], 
            bins=band_edges, 
            labels=band_labels,
            include_lowest=True
        )
        
        # Calculate revenue band impacts using groupby
        band_start = time.time()
        
        baseline_by_band = all_baseline.groupby('revenue_band').agg({
            'vat_liability': lambda x: (x * all_baseline.loc[x.index, 'weight']).sum(),
            'weight': 'sum'
        })
        
        reform_by_band = all_reform.groupby('revenue_band').agg({
            'vat_liability': lambda x: (x * all_reform.loc[x.index, 'weight']).sum(),
            'weight': 'sum'
        })
        
        # Calculate firms affected per band
        all_baseline['changed'] = all_baseline['vat_liability'] != all_reform['vat_liability']
        affected_by_band = all_baseline[all_baseline['changed']].groupby('revenue_band')['weight'].sum()
        
        logger.info(f"Revenue band analysis completed in {time.time() - band_start:.3f}s")
        
        # Format revenue band impacts
        band_results = []
        for i, (min_rev, max_rev, band_label) in enumerate(self.revenue_bands):
            baseline_vat = baseline_by_band.loc[band_label, 'vat_liability'] if band_label in baseline_by_band.index else 0
            reform_vat = reform_by_band.loc[band_label, 'vat_liability'] if band_label in reform_by_band.index else 0
            firms_affected = affected_by_band.get(band_label, 0) if band_label in affected_by_band.index else 0
            
            band_results.append({
                "band": band_label,
                "min_revenue": min_rev,
                "max_revenue": max_rev if max_rev != float('inf') else 999999999,
                "baseline_vat": baseline_vat / 1e9,
                "reform_vat": reform_vat / 1e9,
                "revenue_impact": (reform_vat - baseline_vat) / 1e6,
                "firms_affected": int(firms_affected)
            })
        
        total_impact = sum(impact["revenue_impact"] for impact in yearly_impacts)
        
        logger.info(f"Total reform analysis time: {time.time() - start_time:.3f}s")
        
        return {
            "total_impact": total_impact,
            "yearly_impacts": yearly_impacts,
            "revenue_band_impacts": band_results,
            "reform_summary": {
                "registration_threshold": reform.registration_threshold,
                "taper_type": reform.taper_type,
                "taper_start": reform.taper_start,
                "taper_end": reform.taper_end,
                "baseline_thresholds": {
                    year["year"]: year["baseline"] 
                    for year in self.fiscal_years
                }
            }
        }