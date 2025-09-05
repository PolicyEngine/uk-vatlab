"""
VAT Threshold Analysis for Fiscal Year 2026-27
Analyzes the revenue and firm impacts of different VAT registration thresholds.
"""

import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict
from enum import Enum
from pathlib import Path


class TaperType(str, Enum):
    NONE = "none"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class StandaloneVATCalculator:
    def __init__(self, data_path: str = "../synthetic_firms.csv"):
        """Initialize the VAT calculator with synthetic firms data."""
        self.firms_df = pd.read_csv(data_path)
        
        self.fiscal_years = [
            {"year": "2025-26", "baseline": 90000, "firm_growth": 1.0516},
            {"year": "2026-27", "baseline": 90000, "firm_growth": 1.0779},
            {"year": "2027-28", "baseline": 90000, "firm_growth": 1.1102},
            {"year": "2028-29", "baseline": 90000, "firm_growth": 1.1424},
            {"year": "2029-30", "baseline": 90000, "firm_growth": 1.1761},
            {"year": "2030-31", "baseline": 90000, "firm_growth": 1.2114},
        ]
        
        self.vat_rate = 0.20

    def age_data(self, year_index: int) -> pd.DataFrame:
        """Apply growth factors to age the data to a specific year."""
        df = self.firms_df.copy()
        growth_factor = self.fiscal_years[year_index]["firm_growth"]
        
        # Apply growth to firm weights (population growth)
        df['weight'] = df['weight'] * growth_factor
        
        # Apply turnover growth (2.5% per year linear)
        df['annual_turnover_k'] = df['annual_turnover_k'] * (1 + (year_index * 0.025))
        
        return df

    def calculate_vat_liability(self, df: pd.DataFrame, threshold: int, 
                               taper_type: TaperType = TaperType.NONE,
                               taper_start: int = None, 
                               taper_end: int = None) -> pd.DataFrame:
        """Calculate VAT liability based on threshold and taper settings."""
        df = df.copy()
        
        # Convert turnover to pounds for threshold comparison
        df['turnover_pounds'] = df['annual_turnover_k'] * 1000
        # Convert existing VAT liability from thousands to pounds
        df['vat_liability_base'] = df['vat_liability_k'] * 1000
        
        if taper_type != TaperType.NONE:
            # Calculate taper parameters
            if taper_type == TaperType.MODERATE:
                taper_start = max(65000, threshold - 25000)
                taper_end = threshold + 20000
            elif taper_type == TaperType.AGGRESSIVE:
                taper_start = max(50000, threshold - 35000)
                taper_end = threshold + 10000
            elif taper_type == TaperType.CUSTOM:
                taper_start = taper_start or threshold * 0.75
                taper_end = taper_end or threshold
            
            # Calculate taper multiplier
            df['taper_multiplier'] = 0.0
            
            # Firms in taper range get proportional multiplier
            in_taper = (df['turnover_pounds'] >= taper_start) & (df['turnover_pounds'] < taper_end)
            progress = (df.loc[in_taper, 'turnover_pounds'] - taper_start) / (taper_end - taper_start)
            df.loc[in_taper, 'taper_multiplier'] = progress
            
            # Firms above taper end get full multiplier
            above_taper = df['turnover_pounds'] >= taper_end
            df.loc[above_taper, 'taper_multiplier'] = 1.0
            
            # Apply taper to existing VAT liability
            df['vat_liability'] = df['vat_liability_base'] * df['taper_multiplier']
        else:
            # Simple threshold: firms below threshold pay no VAT
            df['is_registered'] = df['turnover_pounds'] >= threshold
            df['vat_liability'] = np.where(
                df['is_registered'],
                df['vat_liability_base'],
                0
            )
        
        return df

    def calculate_revenue_for_threshold(self, threshold: int, year_index: int = 1,
                                       taper_type: TaperType = TaperType.NONE) -> Dict:
        """Calculate VAT revenue for a specific threshold and year."""
        year_info = self.fiscal_years[year_index]
        
        # Age data to the specified year
        df = self.age_data(year_index)
        
        # Calculate baseline VAT (current threshold)
        baseline_df = self.calculate_vat_liability(df.copy(), year_info["baseline"])
        baseline_revenue = (baseline_df['vat_liability'] * baseline_df['weight']).sum()
        
        # Calculate reform VAT (new threshold)
        reform_df = self.calculate_vat_liability(df.copy(), threshold, taper_type)
        reform_revenue = (reform_df['vat_liability'] * reform_df['weight']).sum()
        
        # Calculate impacts
        revenue_change = reform_revenue - baseline_revenue
        
        # Count firms affected
        baseline_registered = baseline_df[baseline_df['vat_liability'] > 0]['weight'].sum()
        reform_registered = reform_df[reform_df['vat_liability'] > 0]['weight'].sum()
        
        return {
            "threshold": threshold,
            "year": year_info["year"],
            "baseline_revenue_billions": baseline_revenue / 1e9,
            "reform_revenue_billions": reform_revenue / 1e9,
            "revenue_change_millions": revenue_change / 1e6,
            "revenue_change_percent": (revenue_change / baseline_revenue) * 100 if baseline_revenue > 0 else 0,
            "firms_affected": int(abs(reform_registered - baseline_registered)),
            "newly_registered": int(max(0, reform_registered - baseline_registered)),
            "newly_deregistered": int(max(0, baseline_registered - reform_registered))
        }

    def calculate_revenue_curve(self, thresholds: list, year_index: int = 1,
                              taper_type: TaperType = TaperType.NONE) -> pd.DataFrame:
        """Calculate revenue changes for multiple thresholds."""
        results = []
        for threshold in thresholds:
            result = self.calculate_revenue_for_threshold(threshold, year_index, taper_type)
            results.append(result)
        
        return pd.DataFrame(results)


def generate_threshold_chart():
    """Generate threshold vs revenue and firms change charts for 2026-27."""
    # Create results directory if it doesn't exist
    Path("results").mkdir(exist_ok=True)
    
    # Initialize calculator
    print("Loading data and calculating revenue impacts for 2026-27...")
    calculator = StandaloneVATCalculator(data_path="../synthetic_firms.csv")
    
    # Define 11 example thresholds: from 70k to 120k including 90k
    thresholds = [70000, 75000, 80000, 85000, 90000, 95000, 100000, 105000, 110000, 115000, 120000]
    
    # Calculate for 2026-27 fiscal year
    year_index = 1
    fiscal_year = "2026-27"
    
    # Calculate results
    results = calculator.calculate_revenue_curve(
        thresholds, year_index=year_index, taper_type=TaperType.NONE
    )
    
    # Prepare data for Plotly Express
    results['threshold_k'] = results['threshold'] / 1000
    results['firms_k'] = results['firms_affected'] / 1000
    results['hover_text'] = results.apply(
        lambda row: f"<b>Threshold: £{int(row['threshold']/1000)}k</b><br>" + 
                   f"Revenue change: {'+'if row['revenue_change_millions'] >= 0 else ''}{row['revenue_change_millions']:.1f}m<br>" +
                   f"Firms affected: {row['firms_affected']/1000:.1f}k",
        axis=1
    )
    
    # Calculate signed change in firms
    results['firms_change'] = results.apply(
        lambda row: row['firms_affected'] if row['threshold'] < 90000 else -row['firms_affected'],
        axis=1
    )
    results['firms_change_k'] = results['firms_change'] / 1000
    
    # Save results to JSON
    json_data = {
        "fiscal_year": fiscal_year,
        "current_threshold": 90000,
        "analysis_date": pd.Timestamp.now().isoformat(),
        "thresholds": results.to_dict(orient="records")
    }
    
    json_path = f"results/threshold_analysis_{fiscal_year.replace('-', '_')}.json"
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"JSON data saved to {json_path}")
    
    # Create revenue change chart
    fig = px.scatter(results, 
                     x='threshold_k', 
                     y='revenue_change_millions',
                     custom_data=['hover_text'])
    
    # Update traces for line with markers
    fig.update_traces(
        mode='lines+markers',
        line=dict(color='darkblue', width=4),
        marker=dict(
            color='darkblue',
            size=12,
            opacity=0.8,
            line=dict(color='darkblue', width=1.5)
        ),
        hovertemplate='%{customdata[0]}<extra></extra>',
        showlegend=False
    )
    
    # Add reference lines
    fig.add_hline(y=0, line_width=2, line_color="black")
    fig.add_vline(x=90, line_width=1.5, line_dash="dash", line_color="black", opacity=0.5)
    
    # Add annotation
    fig.add_annotation(
        x=91, y=1050,
        text="Current £90k",
        showarrow=False,
        font=dict(size=16, color="black"),
        xanchor='left'
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"Impact of VAT threshold changes on tax revenue ({fiscal_year})",
            x=0.5,
            xanchor='center',
            font=dict(size=24)
        ),
        xaxis_title=dict(text="Registration threshold (£k)", font=dict(size=18)),
        yaxis_title=dict(text="Revenue (£m)", font=dict(size=18)),
        font=dict(family="Arial, sans-serif", size=16),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickmode='array',
            tickvals=results['threshold'] / 1000,
            ticktext=[f'{int(x)}' for x in results['threshold'] / 1000],
            showgrid=True,
            gridcolor='rgba(0,0,0,0.15)',
            griddash='solid',
            zeroline=False,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            tickfont=dict(size=16)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.15)',
            griddash='solid',
            zeroline=False,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            tickfont=dict(size=16)
        ),
        showlegend=False,
        hovermode='closest',
        height=600,
        width=1000,
        margin=dict(l=100, r=50, t=80, b=80)
    )
    
    # Save revenue chart
    output_html = f'results/revenue_impact_{fiscal_year.replace("-", "_")}.html'
    fig.write_html(
        output_html,
        config={'displayModeBar': True, 'displaylogo': False},
        include_plotlyjs='cdn'
    )
    
    output_path = f'results/revenue_impact_{fiscal_year.replace("-", "_")}.png'
    fig.write_image(output_path, width=1200, height=700, scale=2)
    print(f"Revenue chart saved to {output_html} and {output_path}")
    
    # Create firms change chart
    fig2 = px.scatter(results, 
                     x='threshold_k', 
                     y='firms_change_k',
                     custom_data=['hover_text'])
    
    # Update traces for line with markers
    fig2.update_traces(
        mode='lines+markers',
        line=dict(color='darkblue', width=4),
        marker=dict(
            color='darkblue',
            size=12,
            opacity=0.8,
            line=dict(color='darkblue', width=1.5)
        ),
        hovertemplate='%{customdata[0]}<extra></extra>',
        showlegend=False
    )
    
    # Add reference lines
    fig2.add_hline(y=0, line_width=2, line_color="black")
    fig2.add_vline(x=90, line_width=1.5, line_dash="dash", line_color="black", opacity=0.5)
    
    # Add annotation
    fig2.add_annotation(
        x=91, y=40,
        text="Current £90k",
        showarrow=False,
        font=dict(size=16, color="black"),
        xanchor='left',
        yanchor='top'
    )
    
    # Update layout for firms chart
    fig2.update_layout(
        title=dict(
            text=f"Change in VAT-paying firms by threshold ({fiscal_year})",
            x=0.5,
            xanchor='center',
            font=dict(size=24)
        ),
        xaxis_title=dict(text="Registration threshold (£k)", font=dict(size=18)),
        yaxis_title=dict(text="Change in number of firms (thousands)", font=dict(size=18)),
        font=dict(family="Arial, sans-serif", size=16),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            tickmode='array',
            tickvals=results['threshold'] / 1000,
            ticktext=[f'{int(x)}' for x in results['threshold'] / 1000],
            showgrid=True,
            gridcolor='rgba(0,0,0,0.15)',
            griddash='solid',
            zeroline=False,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            tickfont=dict(size=16)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.15)',
            griddash='solid',
            zeroline=False,
            showline=True,
            linewidth=2,
            linecolor='black',
            mirror=True,
            tickfont=dict(size=16),
            tickformat='.0f'
        ),
        showlegend=False,
        hovermode='closest',
        height=600,
        width=1000,
        margin=dict(l=100, r=50, t=80, b=80)
    )
    
    # Save firms chart
    output_firms_html = f'results/firms_impact_{fiscal_year.replace("-", "_")}.html'
    fig2.write_html(
        output_firms_html,
        config={'displayModeBar': True, 'displaylogo': False},
        include_plotlyjs='cdn'
    )
    
    output_firms_path = f'results/firms_impact_{fiscal_year.replace("-", "_")}.png'
    fig2.write_image(output_firms_path, width=1200, height=700, scale=2)
    print(f"Firms chart saved to {output_firms_html} and {output_firms_path}")
    
    # Print summary table
    print("\n" + "="*70)
    print(f"REVENUE IMPACT SUMMARY - Fiscal Year {fiscal_year}")
    print("(Current threshold: £90k)")
    print("="*70)
    print(f"{'Threshold':>12} | {'Revenue Change':>15} | {'Firms Affected (in 1,000)':>25}")
    print("-"*70)
    
    for _, row in results.iterrows():
        threshold_str = f"£{int(row['threshold']/1000)}k"
        revenue_str = f"{'+'if row['revenue_change_millions'] >= 0 else ''}{row['revenue_change_millions']:.1f}m"
        firms_str = f"{row['firms_affected']/1000:.1f}"
        
        print(f"{threshold_str:>12} | {revenue_str:>15} | {firms_str:>25}")
    
    print("="*70)
    
    return results


if __name__ == "__main__":
    results = generate_threshold_chart()