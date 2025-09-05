from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import PolicyReform, PolicyAnalysisResult
from vat_calculator import VATCalculator
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VAT Policy Analysis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global calculator instance - load data once at startup
_calculator = None

def get_calculator():
    """Get or create calculator instance."""
    global _calculator
    if _calculator is None:
        start = time.time()
        _calculator = VATCalculator()
        logger.info(f"Calculator instantiation took {time.time() - start:.3f}s")
    return _calculator


@app.get("/")
async def root():
    return {
        "message": "VAT Policy Analysis API",
        "endpoints": {
            "/analyze": "POST - Analyze a VAT reform policy",
            "/baseline": "GET - Get baseline VAT statistics",
            "/docs": "GET - API documentation"
        }
    }


@app.get("/baseline")
async def get_baseline():
    """Get baseline VAT statistics across all years."""
    try:
        calculator = get_calculator()
        baseline_stats = []
        for i, year_info in enumerate(calculator.fiscal_years):
            df = calculator.age_data(i)
            baseline_df = calculator.calculate_vat_liability(df, year_info["baseline"])
            
            total_revenue = (baseline_df['vat_liability'] * baseline_df['weight']).sum()
            registered_firms = baseline_df[baseline_df['vat_liability'] > 0]['weight'].sum()
            
            baseline_stats.append({
                "year": year_info["year"],
                "threshold": year_info["baseline"],
                "total_revenue_billions": total_revenue / 1e9,
                "registered_firms": int(registered_firms),
                "growth_factor": year_info["firm_growth"]
            })
        
        return {"baseline_statistics": baseline_stats}
    except KeyError as ke:
        logger.error(f"Missing column in baseline: {str(ke)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Data processing error: {str(ke)}")
    except Exception as e:
        logger.error(f"Error calculating baseline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=PolicyAnalysisResult)
async def analyze_reform(reform: PolicyReform):
    """Analyze the impact of a VAT reform policy."""
    try:
        logger.info(f"Analyzing reform: {reform}")
        
        if reform.registration_threshold < 0 or reform.registration_threshold > 500000:
            raise ValueError("Registration threshold must be between £0 and £500,000")
        
        if reform.taper_type != "none" and reform.taper_type == "custom":
            if not reform.taper_start or not reform.taper_end:
                raise ValueError("Custom taper requires taper_start and taper_end")
            if reform.taper_start >= reform.taper_end:
                raise ValueError("Taper start must be less than taper end")
        
        calculator = get_calculator()
        result = calculator.analyze_reform(reform)
        
        return PolicyAnalysisResult(**result)
    
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except KeyError as ke:
        logger.error(f"Missing column: {str(ke)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Data processing error: {str(ke)}")
    except Exception as e:
        logger.error(f"Error analyzing reform: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}