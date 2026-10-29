# Model comparison

Both models use the same machine-disjoint train, validation, and test partitions.
The champion is selected by validation PR-AUC; held-out test metrics do not take
part in model selection.

| Model | Validation PR-AUC | Test PR-AUC | Test precision | Test recall | Event recall | FP hourly decisions / machine-week |
|---|---:|---:|---:|---:|---:|---:|
| logistic_regression | 0.884 | 0.858 | 0.740 | 0.870 | 96.8% | 1.116 |
| hist_gradient_boosting | 0.987 | 1.000 | 0.997 | 1.000 | 100.0% | 0.011 |

**Champion: `hist_gradient_boosting`**

Selection metric: `average_precision`. MLflow experiment:
`azure-pdm-24h-failure`. Run IDs are recorded in `comparison.json`.

The public dataset is simulated. This comparison validates the training and
experiment-management workflow rather than expected performance on a real fleet.
