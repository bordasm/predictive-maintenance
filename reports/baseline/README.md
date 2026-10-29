# Logistic-regression baseline

Objective: predict any component failure within the next 24 hours.

| Metric | Validation | Held-out test |
|---|---:|---:|
| Average precision (PR-AUC) | 0.884 | 0.858 |
| Precision | 0.817 | 0.740 |
| Recall | 0.891 | 0.870 |
| F1 | 0.853 | 0.799 |
| False-positive hourly decisions / machine-week | 0.714 | 1.116 |

The decision threshold (0.950) was selected on validation data.
The test partition contains complete machines that appear in neither training nor
validation. At that threshold, the model detected 122
of 126 eligible test failure events
(96.8% event recall), with a median lead time of 24.0 hours.

These results measure performance on a public simulated dataset. They demonstrate
the pipeline and evaluation method; they are not evidence of production performance
on a different machine fleet.
