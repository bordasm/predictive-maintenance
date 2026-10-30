# Temporal sequence challenger comparison

All models are evaluated on the same complete `48`-hour
window endpoints from machine-disjoint validation and test fleets. The LSTM and
Transformer receive only the current and preceding observations. Preprocessing
statistics and categories are fitted on training machines only.

| Model | Validation PR-AUC | Test PR-AUC | Test precision | Test recall | Event recall | Training seconds |
|---|---:|---:|---:|---:|---:|---:|
| lstm | 0.9864 | 0.9826 | 0.9157 | 0.9737 | 100.0% | 17.4 |
| transformer | 0.9971 | 0.9939 | 0.9583 | 0.9821 | 100.0% | 38.7 |
| hist_gradient_boosting_incumbent | 0.9999 | 0.9999 | 0.9986 | 1.0000 | 100.0% | existing |

**Sequence champion:** `transformer`  
**Overall validation champion:** `hist_gradient_boosting_incumbent`

The sequence champion did not outperform the deployed tabular incumbent on validation
PR-AUC. Held-out test results are reported after selection and do not choose the
model.

The neural checkpoint has a temporal-window serving contract and is deliberately
kept out of the current single-observation promotion workflow. Online deployment
would first require a stateful feature/window service and a versioned sequence
request contract.
