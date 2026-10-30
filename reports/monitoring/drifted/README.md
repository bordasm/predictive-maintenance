# Injected-voltage-drift monitoring demonstration

**Overall status:** `critical`  
**Rows:** 5000

## Data quality

- Status: **normal**
- Duplicate observation fraction: **0.00%**
- Features containing nulls: **0**

## Strongest numeric drift signals

| Feature | PSI | Status | Out of range |
|---|---:|---|---:|
| `volt` | 12.4339 | critical | 46.24% |
| `volt_mean_3h` | 12.4339 | critical | 69.46% |
| `volt_mean_24h` | 12.4339 | critical | 100.00% |
| `vibration_std_24h` | 0.0043 | normal | 0.00% |
| `days_since_comp2_maintenance` | 0.0037 | normal | 0.00% |
| `rotate` | 0.0033 | normal | 0.02% |
| `pressure_std_24h` | 0.0033 | normal | 0.00% |
| `rotate_std_24h` | 0.0032 | normal | 0.00% |
| `vibration_mean_24h` | 0.0031 | normal | 0.02% |
| `days_since_comp3_maintenance` | 0.0031 | normal | 0.00% |

## Prediction distribution

- PSI: **5.7255** (critical)
- Mean failure probability: **0.0279**
- Alert rate: **2.04%**

## Delayed-label performance

- Labeled rows: **5000** (100.00% coverage)
- Average precision: **0.9497**
- Precision / recall / F1: **0.8235 / 1.0000 / 0.9032**

## Interpretation

PSI below 0.10 is normal, 0.10–0.20 is a warning, and 0.20 or above is critical in this project. A critical result is a review trigger; it does not automatically retrain or promote a model.
