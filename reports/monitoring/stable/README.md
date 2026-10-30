# Stable-window monitoring demonstration

**Overall status:** `normal`  
**Rows:** 5000

## Data quality

- Status: **normal**
- Duplicate observation fraction: **0.00%**
- Features containing nulls: **0**

## Strongest numeric drift signals

| Feature | PSI | Status | Out of range |
|---|---:|---|---:|
| `vibration_std_24h` | 0.0043 | normal | 0.00% |
| `days_since_comp2_maintenance` | 0.0037 | normal | 0.00% |
| `rotate` | 0.0033 | normal | 0.02% |
| `pressure_std_24h` | 0.0033 | normal | 0.00% |
| `rotate_std_24h` | 0.0032 | normal | 0.00% |
| `volt_mean_3h` | 0.0032 | normal | 0.00% |
| `vibration_mean_24h` | 0.0031 | normal | 0.02% |
| `days_since_comp3_maintenance` | 0.0031 | normal | 0.00% |
| `volt_std_24h` | 0.0027 | normal | 0.02% |
| `volt` | 0.0027 | normal | 0.00% |

## Prediction distribution

- PSI: **0.0019** (normal)
- Mean failure probability: **0.0170**
- Alert rate: **1.68%**

## Delayed-label performance

- Labeled rows: **5000** (100.00% coverage)
- Average precision: **1.0000**
- Precision / recall / F1: **1.0000 / 1.0000 / 1.0000**

## Interpretation

PSI below 0.10 is normal, 0.10–0.20 is a warning, and 0.20 or above is critical in this project. A critical result is a review trigger; it does not automatically retrain or promote a model.
