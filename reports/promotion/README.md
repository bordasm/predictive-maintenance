# Model promotion decision

**Decision:** `approved`  
**Candidate:** `hist_gradient_boosting` / `2693190d160d4c37bd6dbb72f215e057`  
**Incumbent:** `hist_gradient_boosting` / `97293e9d3f3a456998d7785bc1ac9f72`

| Gate | Candidate | Requirement | Result |
|---|---:|---:|---|
| minimum validation average precision | 0.986577 | >= 0.850000 | pass |
| maximum validation regression from incumbent | 0.986577 | >= 0.981577 | pass |
| minimum test average precision | 0.999923 | >= 0.850000 | pass |
| minimum test precision | 0.996859 | >= 0.900000 | pass |
| minimum test event recall | 1.000000 | >= 0.950000 | pass |
| maximum false positives per machine-week | 0.011475 | <= 0.100000 | pass |

The gate uses validation performance for relative model selection and held-out
test metrics for absolute operational safeguards. Approval creates no deployment
by itself; promotion remains an explicit command and produces an immutable,
rollback-ready release directory.
