# Synthetic UK Business Population Generator

## Overview

This module generates a comprehensive synthetic dataset of UK business firms, calibrated to match official government statistics from the Office for National Statistics (ONS) and HM Revenue & Customs (HMRC). The generated data includes individual firm records with turnover, employment, sector classification, and VAT registration status.

## Purpose

The synthetic data generator serves multiple analytical purposes:

1. **Privacy-preserving analysis**: Create realistic firm-level data without exposing actual business information
2. **Policy simulation**: Generate large-scale datasets for analyzing VAT policy changes and threshold effects
3. **Academic research**: Provide researchers with granular business data calibrated to official statistics
4. **Bunching analysis**: Generate data specifically designed for VAT threshold bunching studies

## Data Sources

### ONS (Office for National Statistics)
- **Business structure data**: Total firm counts by sector and turnover band
- **Employment data**: Firm employment distribution by size bands
- **Coverage**: All UK businesses (VAT-registered and non-VAT-registered)

### HMRC (HM Revenue & Customs)
- **VAT population by turnover band**: VAT-registered firms by revenue brackets
- **VAT population by sector**: VAT-registered firms by SIC code
- **Coverage**: Only VAT-registered businesses (mandatory + voluntary registration)

## Key Features

### 1. Multi-Source Calibration
- **Dual calibration**: Matches both ONS total population and HMRC VAT-registered subpopulation
- **Multi-objective optimization**: Simultaneously calibrates to multiple target distributions
- **Weighted resampling**: Uses optimization to determine firm weights for accurate representation

### 2. Realistic Business Characteristics

**Turnover Distribution:**
```python
# ONS turnover bands with realistic intra-band variation
band_params = {
    '0-49': (0, 49, 24.5),           # £0-49k
    '50-99': (50, 99, 74.5),         # £50-99k  
    '100-249': (100, 249, 174.5),    # £100-249k
    '250-499': (250, 499, 374.5),    # £250-499k
    '500-999': (500, 999, 749.5),    # £500-999k
    '1000-4999': (1000, 4999, 2999.5), # £1M-5M
    '5000+': (5000, 50000, 15000)    # £5M+
}
```

**Employment Distribution:**
```python
# ONS employment bands with sector-specific patterns
employment_bands = ['0-4', '5-9', '10-19', '20-49', '50-99', '100-249', '250+']
```

**VAT Registration Logic:**
```python
# Mandatory: Annual turnover > £90k (2023-24 threshold)
mandatory_vat = turnover_values > 90.0

# Voluntary: Calibrated rate for firms below threshold
voluntary_rate = hmrc_target_below_threshold / synthetic_count_below_threshold
```

### 3. Advanced Technical Implementation

**PyTorch Backend:**
- Efficient tensor operations for large-scale data generation
- GPU support for accelerated processing (optional)
- Memory-efficient batch processing

**Optimization Framework:**
- Multi-objective loss function with symmetric relative error
- Adam optimizer with gradient clipping
- Early stopping with patience mechanism
- Dropout regularization during training

## Mathematical Framework

### Target Matrix Construction

The calibration process uses a target matrix **A** where A[i,j] represents the contribution of firm j to target i:

```python
# Target matrix dimensions: (n_targets, n_firms)
n_targets = 7 + n_sectors + n_employment_bands
target_matrix = torch.zeros(n_targets, n_firms)

# Turnover targets (rows 0-6)
for band_idx in range(7):
    firms_in_band = (turnover_band_indices == band_idx)
    target_matrix[band_idx, firms_in_band] = 1.0

# Sector targets (rows 7 to 7+n_sectors-1)  
for sector_idx, sic_code in enumerate(sector_codes):
    firms_in_sector = (sic_codes == sic_code)
    target_matrix[7 + sector_idx, firms_in_sector] = 1.0
```

### Optimization Objective

**Symmetric Relative Error Loss:**
```
L = Σᵢ wᵢ × min(|pred_i/target_i - 1|², |target_i/pred_i - 1|²)
```

Where:
- pred_i = predicted count for target i
- target_i = official target count for target i  
- wᵢ = importance weight for target i

**Importance Weights:**
- Turnover targets: 5.0× (most critical for VAT analysis)
- Sector targets: 1.0× (important for representativeness)
- Employment targets: 1.0× (important for firm size distribution)

### Weight Optimization

```python
# Initialize log-weights (ensures positive weights)
log_weights = torch.zeros(n_firms, requires_grad=True)
optimizer = torch.optim.Adam([log_weights], lr=0.01)

# Convert to positive weights
weights = torch.exp(log_weights)

# Calculate predictions
predictions = torch.matmul(target_matrix, weights)

# Apply dropout for regularization (95% keep rate)
dropout_mask = torch.rand_like(weights) > 0.05
weights = weights * dropout_mask
```

## Generated Dataset Schema

The output CSV file contains the following columns:

| Column | Type | Description | Range/Values |
|--------|------|-------------|-------------|
| `sic_code` | string | 5-digit SIC 2007 code | '00001' - '99999' |
| `annual_turnover_k` | float | Annual turnover in £thousands | 0.0 - 50000.0 |
| `employment` | int | Number of employees | 1 - 2000 |
| `weight` | float | Calibration weight | 0.1 - 10.0 |
| `vat_registered` | bool | VAT registration status | True/False |

### Example Records:
```csv
sic_code,annual_turnover_k,employment,weight,vat_registered
01110,45.7,3,1.2,False
01120,156.8,12,0.9,True
01130,0.0,1,1.0,False
...
```

## Usage

### Basic Usage

```python
from generate_synthetic_data import SyntheticFirmGenerator

# Initialize generator
generator = SyntheticFirmGenerator(
    device="cpu",      # Use "cuda" or "mps" for GPU acceleration
    random_seed=42     # For reproducible results
)

# Generate synthetic data
synthetic_df = generator.generate_synthetic_firms()

# Save to CSV
synthetic_df.to_csv('synthetic_firms_turnover.csv', index=False)
```

### Advanced Configuration

```python
# Custom device selection
device = "cuda" if torch.cuda.is_available() else "cpu"
generator = SyntheticFirmGenerator(device=device)

# Access individual components
ons_df, ons_employment_df, hmrc_turnover_df, hmrc_sector_df, ons_total = generator.load_data()

# Generate with custom optimization parameters
target_matrix, target_values = generator.create_comprehensive_target_matrix(
    turnover_values, sic_codes, hmrc_bands, hmrc_sector_df, ons_employment_df, ons_total
)

optimized_weights = generator.optimize_weights(
    target_matrix, target_values,
    n_iterations=500,  # More iterations for better fit
    lr=0.005          # Lower learning rate for stability
)
```

## Validation Framework

### Multi-Source Validation

The generator validates synthetic data against all source datasets:

**1. HMRC VAT Registration Validation:**
- Total VAT-registered firm count
- VAT-registered firms by turnover band
- VAT-registered firms by sector

**2. ONS Population Validation:**
- Total UK business population
- Firm distribution by turnover band
- Firm distribution by employment size

**3. Consistency Checks:**
- Mass conservation (total firms unchanged)
- Distribution smoothness
- Sector representation

### Accuracy Metrics

```python
def validate_accuracy(synthetic_count, target_count):
    """Calculate accuracy as 1 - relative_absolute_error"""
    if target_count > 0:
        return 1 - abs(synthetic_count - target_count) / target_count
    else:
        return 1.0 if synthetic_count == 0 else 0.0

# Accuracy thresholds:
# ≥95%: Excellent calibration
# 90-95%: Good calibration  
# 80-90%: Acceptable calibration
# <80%: Poor calibration
```

### Example Validation Output:

```
CALIBRATION SUMMARY
================================================================================
HMRC Turnover Bands: 94.2%
ONS Population:      98.7%
Employment Bands:    91.5%
Sector Distribution: 89.3%
Overall Accuracy:    93.4%
Total Population: 2,944,000 firms
```

## Output Statistics

### Typical Dataset Characteristics:
- **Total firms**: ~2.94 million (calibrated to ONS total)
- **VAT-registered firms**: ~2.2 million (calibrated to HMRC total)
- **File size**: ~150-200 MB CSV
- **Generation time**: 2-5 minutes (CPU), 30 seconds - 1 minute (GPU)
- **Memory usage**: 2-4 GB peak

### Turnover Distribution:
- **Below £90k**: ~678k firms (23% of total, mostly non-VAT)
- **£90k-£150k**: ~535k firms (18% of total, all VAT-registered)
- **Above £150k**: ~1.7M firms (59% of total, all VAT-registered)

### Employment Distribution:
- **Micro (0-9 employees)**: ~2.4M firms (82% of total)
- **Small (10-49 employees)**: ~420k firms (14% of total)
- **Medium+ (50+ employees)**: ~120k firms (4% of total)

## Technical Requirements

### Dependencies:
```python
torch>=1.9.0      # PyTorch for tensor operations
pandas>=1.3.0     # Data manipulation
numpy>=1.20.0     # Numerical computing
pathlib>=1.0      # Path handling
logging>=1.0      # Logging framework
```

### System Requirements:
- **RAM**: 4-8 GB recommended
- **Storage**: 1 GB free space for output files
- **CPU**: Multi-core recommended for faster processing
- **GPU**: Optional (CUDA/ROCm for acceleration)

### Installation:
```bash
# Install required packages
pip install torch pandas numpy

# Run generation
python generate_synthetic_data.py
```

## Data Directory Structure

```
PolicyEngine_VATLab/
├── analysis/
│   ├── generate_synthetic_data.py          # Main generator script
│   └── synthetic_firms_turnover.csv        # Generated output
└── data/
    ├── ONS_UK_business_data/
    │   ├── firm_turnover.csv               # ONS turnover data
    │   └── firm_employment.csv             # ONS employment data
    └── HMRC_VAT_annual_statistics/
        ├── vat_population_by_turnover_band.csv  # HMRC turnover bands
        └── vat_population_by_sector.csv         # HMRC sector data
```

## Quality Assurance

### Data Quality Checks:
1. **Completeness**: No missing values in required fields
2. **Consistency**: VAT flags consistent with turnover thresholds
3. **Realism**: Turnover and employment distributions match empirical patterns
4. **Calibration**: Multi-source targets achieved within accuracy tolerances

### Robustness Testing:
- **Seed sensitivity**: Results stable across different random seeds
- **Parameter sensitivity**: Robust to optimization hyperparameter changes
- **Scale testing**: Handles different population sizes efficiently
- **Memory testing**: Efficient memory usage for large datasets

## Applications

### 1. VAT Bunching Analysis
The synthetic data is specifically designed for analyzing firm responses to VAT registration thresholds:

```python
# Filter firms near VAT threshold
near_threshold = synthetic_df[
    (synthetic_df['annual_turnover_k'] >= 70) & 
    (synthetic_df['annual_turnover_k'] <= 110)
]

# Analyze bunching patterns
bunching_analysis = analyze_threshold_bunching(near_threshold)
```

### 2. Policy Impact Simulation
Simulate effects of changing VAT thresholds or rates:

```python
# Simulate threshold increase from £90k to £100k
new_policy_data = simulate_threshold_change(
    synthetic_df, 
    old_threshold=90, 
    new_threshold=100
)
```

### 3. Firm Size Distribution Analysis
Study the relationship between turnover, employment, and sector:

```python
# Analyze firm size patterns by sector
size_analysis = synthetic_df.groupby('sic_code').agg({
    'annual_turnover_k': 'mean',
    'employment': 'mean',
    'weight': 'sum'
}).reset_index()
```

## Methodological Notes

### Calibration Strategy
1. **Two-stage approach**: First generate from ONS structure, then calibrate to HMRC targets
2. **Constrained optimization**: Preserve ONS population structure while matching HMRC VAT patterns
3. **Multi-objective**: Balance multiple targets simultaneously rather than sequential fitting

### VAT Registration Modeling
- **Mandatory registration**: Automatic for firms >£90k turnover
- **Voluntary registration**: Probabilistic based on HMRC data calibration
- **Realistic patterns**: Higher registration rates for larger firms and B2B sectors

### Limitations
- **Static snapshot**: Represents single year (2023-24), not dynamic behavior
- **Simplified sectors**: Uses major SIC categories, not full granular classification
- **Regional variation**: No geographic distribution (UK-wide averages)
- **Firm dynamics**: No modeling of entry/exit or growth patterns

## References

1. **ONS Business Structure Database**: UK business population statistics by turnover and employment
2. **HMRC VAT Statistics**: Annual statistics on VAT-registered businesses
3. **SIC 2007 Classification**: Standard Industrial Classification codes for sector assignment
4. **PyTorch Documentation**: Technical framework for tensor operations and optimization