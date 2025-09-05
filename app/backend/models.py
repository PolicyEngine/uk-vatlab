from pydantic import BaseModel
from typing import Optional, Dict, List
from enum import Enum


class TaperType(str, Enum):
    NONE = "none"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class PolicyReform(BaseModel):
    registration_threshold: int
    taper_type: TaperType = TaperType.NONE
    taper_start: Optional[int] = None
    taper_end: Optional[int] = None
    taper_rate: Optional[float] = None


class YearlyImpact(BaseModel):
    year: str
    baseline_revenue: float
    reform_revenue: float
    revenue_impact: float
    firms_affected: int
    newly_registered: int
    newly_deregistered: int


class SectorImpact(BaseModel):
    sector: str
    baseline_revenue: float
    reform_revenue: float
    revenue_impact: float
    firms_affected: int


class RevenueBandImpact(BaseModel):
    band: str
    min_revenue: float
    max_revenue: float
    baseline_vat: float
    reform_vat: float
    revenue_impact: float
    firms_affected: int


class PolicyAnalysisResult(BaseModel):
    total_impact: float
    yearly_impacts: List[YearlyImpact]
    revenue_band_impacts: List[RevenueBandImpact]
    reform_summary: Dict