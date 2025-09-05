export interface PolicyReform {
  registration_threshold: number;
  taper_type: 'none' | 'moderate' | 'aggressive' | 'custom';
  taper_start?: number;
  taper_end?: number;
  taper_rate?: number;
}

export interface YearlyImpact {
  year: string;
  baseline_revenue: number;
  reform_revenue: number;
  revenue_impact: number;
  firms_affected: number;
  newly_registered: number;
  newly_deregistered: number;
}

export interface SectorImpact {
  sector: string;
  baseline_revenue: number;
  reform_revenue: number;
  revenue_impact: number;
  firms_affected: number;
}

export interface RevenueBandImpact {
  band: string;
  min_revenue: number;
  max_revenue: number;
  baseline_vat: number;
  reform_vat: number;
  revenue_impact: number;
  firms_affected: number;
}

export interface PolicyAnalysisResult {
  total_impact: number;
  yearly_impacts: YearlyImpact[];
  revenue_band_impacts: RevenueBandImpact[];
  unique_firms_affected: number;
  reform_summary: {
    registration_threshold: number;
    taper_type: string;
    taper_start?: number;
    taper_end?: number;
    baseline_thresholds: Record<string, number>;
  };
}
