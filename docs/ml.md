# Machine Learning Specification

## 1. Purpose

This document defines the final machine-learning architecture, methodology, evaluation strategy, model lifecycle, inference behavior, monitoring relationship, and retraining controls implemented in the Building & Energy Intelligence Platform.

The machine-learning system is designed as a complete, reproducible lifecycle rather than as an isolated model-training notebook:

```text
Historical Data
      ↓
Data Validation
      ↓
Feature Engineering
      ↓
Baseline Evaluation
      ↓
Learned Model Training
      ↓
Validation / Test Evaluation
      ↓
Experiment Tracking
      ↓
Model Registry
      ↓
Promotion Decision
      ↓
Production Serving
      ↓
Inference
      ↓
Monitoring
      ↓
Degradation Assessment
      ↓
Retraining Eligibility
      ↓
Candidate Retraining
      ↓
Evaluation
      ↓
Promotion or Rejection
````

The final implementation deliberately separates:

* model training from model serving
* monitoring from retraining
* candidate models from production models
* drift detection from promotion decisions
* learned models from the persistence baseline
* model registration from production activation

No model is promoted merely because it was trained successfully.

---

# 2. Prediction Objective

The primary machine-learning task is **next-hour building electricity consumption forecasting**.

The target variable is:

```text
target_next_hour_kwh
```

For a given building and prediction timestamp, the system estimates electricity consumption for the following hour using:

* historical energy consumption
* weather conditions
* building metadata
* calendar/time information
* lagged energy features
* rolling energy statistics
* heating/cooling degree-hour features

The inference pipeline uses a **168-hour historical context window** to construct the required temporal features.

This corresponds to seven days of hourly history.

---

# 3. Data Used by the ML System

The model-development pipeline uses the processed BDG2 dataset generated during the data and feature-engineering stages.

Canonical feature dataset:

```text
data/processed/phase1_features.parquet
```

The processed dataset contains:

```text
210,528 rows
44 columns
```

The prediction target is:

```text
target_next_hour_kwh
```

The selected dataset covers:

```text
12 buildings
2016-01-01 through 2017-12-31
```

The raw data sources are:

```text
data/raw/bdg2/electricity_cleaned.csv
data/raw/bdg2/metadata.csv
data/raw/bdg2/weather.csv
```

The ML pipeline does not directly train against arbitrary raw CSV structures. Feature generation produces the canonical processed representation consumed by model training and evaluation.

---

# 4. Feature Engineering

Feature engineering is implemented as a deterministic preprocessing stage.

The feature set contains several categories.

## 4.1 Energy History Features

Historical electricity consumption provides the principal temporal signal.

The pipeline generates lagged consumption features from previous observations, including temporal history required to represent:

* recent consumption
* previous-day behavior
* previous-week behavior

Rolling statistics are also used to represent recent consumption patterns.

These features allow the learned models to capture temporal persistence and short-term consumption structure.

---

## 4.2 Weather Features

Weather information is incorporated into the prediction feature set.

Relevant variables include:

```text
air_temperature
dew_temperature
sea_level_pressure
wind_direction
wind_speed
cloud_coverage
precip_depth_1_hr
```

Weather variables are aligned with the building observations before feature generation.

---

## 4.3 Building Metadata

Building-level metadata is included in the feature representation.

The feature set contains building/site identifiers and building characteristics available from the BDG2 metadata.

Examples include:

```text
building_id
site_id
primary_use
square_feet
floor_area
```

Categorical building information is represented in the model-compatible feature representation.

---

## 4.4 Calendar Features

Temporal features represent recurring time patterns.

The feature representation includes information derived from timestamps such as:

```text
hour
day
day-of-week
month
```

These features allow the learned models to distinguish different recurring consumption periods.

---

## 4.5 Degree-Hour Features

Heating and cooling degree-hour features are derived from temperature information.

They provide additional representations of temperature-related building energy demand.

The feature set therefore contains:

```text
heating degree hours
cooling degree hours
```

alongside the raw weather variables.

---

## 4.6 Lag and Rolling Features

The temporal feature pipeline generates lagged and rolling variables using historical energy observations.

The inference service reconstructs these features from the supplied 168-hour history rather than requiring the client to provide precomputed model features.

This establishes a clear boundary:

```text
Prediction Request
      ↓
Inference Feature Construction
      ↓
Model-Compatible Feature Vector
      ↓
Model Prediction
```

---

# 5. Baseline Models

A learned model is not evaluated in isolation.

The project uses simple forecasting strategies as explicit baselines so that model complexity must provide measurable value.

The implemented baselines include:

```text
pred_persistence
pred_previous_day
pred_previous_week
```

The primary baseline is:

```text
pred_persistence
```

The persistence strategy predicts the next value using the most recent observed energy value.

The best baseline recorded during the original evaluation was:

```text
Best baseline:
pred_persistence
NMAE = 0.0592740184411023
```

The baseline comparison is an explicit part of the model-promotion logic.

---

# 6. Learned Models

Three classical machine-learning model families were evaluated.

## 6.1 Ridge Regression

Model family:

```text
ridge
```

Ridge provides a regularized linear reference model.

Original test results:

```text
MAE    = 14.845004
RMSE   = 29.860645
CVRMSE = 20.977587%
NMAE   = 0.104289
```

---

## 6.2 Random Forest

Model family:

```text
random_forest
```

Random Forest provides a nonlinear ensemble model capable of representing interactions between temporal, weather, and building-level features.

Original test results:

```text
MAE    = 10.830353
RMSE   = 24.610103
CVRMSE = 17.288996%
NMAE   = 0.076085
```

---

## 6.3 HistGradientBoosting

Model family:

```text
hist_gradient_boosting
```

HistGradientBoosting provides a gradient-boosted nonlinear model.

Original test results:

```text
MAE    = 11.015266
RMSE   = 24.526046
CVRMSE = 17.229944%
NMAE   = 0.077384
```

The project retains all three model families as evaluated candidates rather than treating one algorithm as universally superior.

---

# 7. Evaluation Metrics

The ML system evaluates forecasting performance using multiple metrics.

## 7.1 Mean Absolute Error

```text
MAE
```

Measures the average absolute prediction error in the target's original unit.

---

## 7.2 Root Mean Squared Error

```text
RMSE
```

Penalizes larger errors more strongly than MAE.

---

## 7.3 Coefficient of Variation of RMSE

```text
CVRMSE
```

Expresses RMSE relative to the relevant consumption scale.

---

## 7.4 Normalized Mean Absolute Error

```text
NMAE
```

Normalizes the absolute error to make model performance easier to compare across buildings and datasets.

---

## 7.5 Macro-Building NMAE

```text
macro_building_nmae
```

The project additionally evaluates the average normalized error across buildings.

This prevents aggregate performance from being dominated by buildings with larger absolute energy consumption.

For lifecycle decisions, the validation metric used for learned-model comparison is:

```text
validation_macro_building_nmae
```

This is intentionally stricter than relying only on a global aggregate metric.

---

# 8. Original Model Evaluation

The original learned-model evaluation produced the following results.

| Model                | Validation MAE | Validation RMSE | Validation CVRMSE | Validation NMAE | Validation Macro-Building NMAE |  Test MAE | Test RMSE | Test CVRMSE | Test NMAE | Test Macro-Building NMAE |
| -------------------- | -------------: | --------------: | ----------------: | --------------: | -----------------------------: | --------: | --------: | ----------: | --------: | -----------------------: |
| Random Forest        |      11.585128 |       28.264663 |        20.061556% |        0.082228 |                       0.127556 | 10.830353 | 24.610103 |  17.288996% |  0.076085 |                 0.143480 |
| HistGradientBoosting |      12.014662 |       29.071060 |        20.633917% |        0.085277 |                       0.355616 | 11.015266 | 24.526046 |  17.229944% |  0.077384 |                 0.362898 |
| Ridge                |      16.439043 |       34.248344 |        24.308625% |        0.116680 |                       4.065300 | 14.845004 | 29.860645 |  20.977587% |  0.104289 |                 4.034583 |

These results are preserved as the original Phase 1 evaluation record.

They are not interpreted as sufficient evidence for production deployment by themselves because the lifecycle also requires comparison with the operational baseline.

---

# 9. Model Registry

MLflow is used for experiment tracking and model registration.

The registered model name is:

```text
building-energy-forecast
```

The MLflow registry stores model versions together with:

* model artifacts
* run identifiers
* model signatures
* parameters
* metrics
* model-family metadata
* lifecycle metadata
* promotion metadata
* baseline-comparison metadata

The inference service can load the registered production model through the MLflow alias:

```text
@production
```

The system therefore separates:

```text
Registered model version
```

from:

```text
Production model
```

Registration alone does not make a model production-ready.

---

# 10. Model Signatures

Registered MLflow models contain input signatures describing the expected feature structure.

The signatures include building and site metadata, weather variables, temporal features, and temporal history-derived features required by the model.

The model artifacts were explicitly verified against the Docker MLflow environment for the original registered versions.

Signature verification passed for:

```text
v1
v2
v3
```

The registered signatures allow the serving layer to validate and construct model inputs without depending on model-family-specific assumptions about feature extraction.

---

# 11. Production Serving Strategy

The model service supports two distinct serving modes:

```text
learned
baseline
```

## 11.1 Learned Serving

When a learned model is available under the configured production alias, the inference service:

1. receives a prediction request
2. validates the request
3. constructs inference features
4. loads the production learned model
5. performs inference
6. clamps the final prediction to a nonnegative value
7. returns the prediction together with model metadata

---

## 11.2 Baseline Serving

When no learned production model is available, the service can operate using the persistence strategy.

The baseline prediction is:

```text
latest observed energy value
```

This is not a fake learned model.

The service explicitly identifies its serving mode as:

```text
baseline
```

and exposes the model/serving metadata through the API.

This allows the platform to remain operational while refusing to claim that a learned model has earned production status.

---

# 12. Production Promotion Gate

The central ML lifecycle rule is:

> A learned model must beat the persistence baseline on the required validation metric before it can become production.

The promotion metric is:

```text
validation_macro_building_nmae
```

The baseline comparison uses the corresponding macro-building baseline metric.

The decision logic is conceptually:

```text
if learned_validation_macro_building_nmae
    < baseline_macro_building_nmae:

    promote learned model

else:

    reject learned model
```

The promotion system also evaluates the relationship to the current production model when a learned production model exists.

Therefore:

```text
Candidate
    ↓
Evaluate
    ↓
Compare with persistence baseline
    ↓
Compare with current production where applicable
    ↓
Promotion decision
```

A candidate cannot bypass the baseline guard simply because it is better than another learned candidate.

---

# 13. Final Phase 6 Retraining Evaluation

Phase 6 introduced a controlled candidate-retraining workflow using simulated production data.

The simulated data contains two modes:

```text
normal
shifted
```

The shifted scenario deliberately changes weather conditions and target behavior to create a controlled distribution/performance-change scenario.

Candidate models were trained from the shifted dataset and registered as:

```text
v4 = Ridge
v5 = Random Forest
v6 = HistGradientBoosting
```

All three candidates were evaluated against the persistence baseline.

The final evaluation was:

| Version | Model                | Candidate NMAE | Persistence NMAE | Decision |
| ------- | -------------------- | -------------: | ---------------: | -------- |
| v4      | Ridge                |      13.008031 |         0.219467 | Rejected |
| v5      | Random Forest        |       9.466449 |         0.219467 | Rejected |
| v6      | HistGradientBoosting |       2.904410 |         0.219467 | Rejected |

The candidates therefore did not satisfy the production baseline gate.

The final MLflow state intentionally contains:

```text
Learned production alias:
NONE
```

This is an intentional lifecycle outcome.

The system does not manufacture a production deployment merely to demonstrate promotion.

---

# 14. Candidate Isolation

Retrained models are registered as candidate versions.

Candidate training does not modify the currently served model.

The lifecycle therefore maintains the separation:

```text
Production Model
       │
       │ remains unchanged
       │
Candidate Model
       │
       └── evaluated independently
```

A candidate may be:

```text
accepted → promoted
```

or:

```text
rejected → retained as registry history
```

without corrupting or silently replacing production state.

---

# 15. Retraining Eligibility

Phase 6 introduces an explicit retraining-eligibility decision before candidate training.

Retraining eligibility considers multiple signals:

```text
sufficient samples
sustained degradation
baseline comparison
data quality
service readiness
drift evidence
```

The lifecycle distinguishes:

```text
drift detected
```

from:

```text
retraining required
```

Drift is therefore a supporting signal rather than an unconditional retraining trigger.

The eligibility system can produce:

```text
retraining_eligible
```

or:

```text
not_eligible
```

This prevents isolated statistical drift from automatically causing unnecessary retraining.

---

# 16. Monitoring and ML Performance

Monitoring is part of the ML lifecycle but is not itself a retraining mechanism.

The monitoring system tracks:

* prediction behavior
* actual outcomes when available
* rolling error metrics
* per-building performance
* global performance
* baseline performance
* feature drift
* data quality
* service readiness
* serving state

Performance metrics include:

```text
MAE
RMSE
NMAE
macro-building NMAE
```

where sufficient prediction/actual pairs are available.

The monitoring architecture is intentionally separated from training.

```text
Monitoring
    ↓
Evidence of degradation
    ↓
Retraining eligibility
    ↓
Candidate training
```

rather than:

```text
Drift
    ↓
Automatic retraining
```

---

# 17. Drift Does Not Equal Retraining

Feature drift can indicate that current production data differs from the reference distribution.

However, drift alone does not establish that a new model will improve predictive performance.

The project therefore treats:

```text
data drift
```

and:

```text
model performance degradation
```

as separate signals.

The lifecycle may use both when determining retraining eligibility.

This design avoids an uncontrolled feedback loop in which every distributional change automatically launches a new training process.

---

# 18. Retraining Dataset

Phase 6 uses controlled production-data simulation to exercise the retraining lifecycle without requiring a live external telemetry source.

The simulator reads:

```text
data/processed/phase1_features.parquet
```

and creates bounded production-like datasets.

Each of the 12 buildings contributes:

```text
168 hourly observations
```

for a total of:

```text
2016 rows
```

The generated files are:

```text
data/interim/production/normal_production.parquet
data/interim/production/shifted_production.parquet
```

The shifted dataset modifies selected weather variables and target behavior to provide a controlled lifecycle test scenario.

These datasets are demonstration and validation inputs for the lifecycle implementation, not claims of real live production telemetry.

---

# 19. Candidate Training Process

The candidate retraining script:

```text
scripts/retrain_candidate.py
```

performs the following workflow:

```text
Select production-like data
        ↓
Validate / prepare dataset
        ↓
Build training features
        ↓
Chronological train/validation split
        ↓
Train candidate model families
        ↓
Evaluate candidates
        ↓
Log runs to MLflow
        ↓
Register candidate versions
```

The candidate training process evaluates the same three learned model families:

```text
Ridge
Random Forest
HistGradientBoosting
```

Candidate models are registered without assigning them the production alias.

---

# 20. Experiment Tracking

MLflow experiment tracking is used to preserve training provenance.

The Phase 6 retraining experiment is:

```text
building-energy-retraining
```

Tracked information includes model-family information, validation metrics, lifecycle status, source mode, and model artifacts.

This makes candidate evaluation reproducible and auditable.

The registry therefore provides a historical record rather than only storing the currently active model.

---

# 21. Model Lifecycle Metadata

Registered model versions may contain metadata describing:

```text
model_family
validation_status
lifecycle_status
promotion_metric
promotion_reason
baseline_guard
baseline_model
baseline_validation_nmae
rejection_reason
source_mode
phase
```

The Model Lab application exposes these registry-level lifecycle details to the user.

This allows the ML system to communicate not only:

```text
what model exists
```

but also:

```text
why the model was or was not promoted
```

---

# 22. Rejection Behavior

A rejected candidate remains part of the MLflow history.

Rejection does not delete the model artifact or erase the experiment.

Instead, the lifecycle records the decision and reason.

For the final Phase 6 candidate models, the rejection condition was:

```text
candidate did not beat persistence
```

The final state therefore preserves the evidence that candidate training occurred while keeping those models out of production.

---

# 23. Rollback

Rollback support is implemented in:

```text
scripts/rollback_model.py
```

Rollback operates through MLflow model aliases.

A rollback requires:

1. an existing learned production model
2. a target registered version
3. the target version to be READY
4. the target version to differ from the current production version

The script records rollback metadata before assigning the target version to:

```text
@production
```

If no learned production model currently exists, rollback is rejected.

The final Phase 6 state intentionally demonstrates this safety behavior:

```text
No learned production model currently exists.
Rollback cannot be demonstrated until a production alias exists.
```

The system does not fabricate a production state solely to demonstrate rollback.

---

# 24. Inference Architecture

The inference boundary is implemented in:

```text
apps/model_service/app/inference.py
```

and exposed through:

```text
apps/model_service/app/main.py
```

The request flow is:

```text
Client
  ↓
FastAPI
  ↓
Request validation
  ↓
Inference service
  ↓
Serving-mode decision
  ├── baseline → persistence prediction
  │
  └── learned
        ↓
     Feature construction
        ↓
     Production model
        ↓
     Prediction
  ↓
Prediction response
```

The inference service uses the same feature definitions expected by the registered model signatures.

---

# 25. Input Validation

Prediction requests are validated through the API schema layer.

The request contains:

* building identifier
* prediction timestamp
* building metadata
* weather information
* historical energy observations

Historical observations must provide the required temporal context.

The service validates:

* timestamp structure
* energy values
* minimum history length
* chronological ordering
* uniqueness of history timestamps
* required request fields

Energy observations are required to be nonnegative.

---

# 26. Prediction Safety

The final learned-model prediction is constrained to a nonnegative value:

```text
max(0.0, prediction)
```

This prevents the API from returning physically implausible negative electricity consumption values.

Baseline inference similarly returns the latest observed nonnegative energy value.

---

# 27. Model Loading

The model-loading layer supports MLflow-backed production serving and local artifact loading for development/testing.

The default test behavior uses:

```text
MODEL_SOURCE=local
```

so unit tests do not depend on an externally running MLflow service.

Production Docker configuration uses MLflow as the model source.

The MLflow serving configuration uses:

```text
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_MODEL_NAME=building-energy-forecast
MLFLOW_MODEL_ALIAS=production
MODEL_SOURCE=mlflow
```

This separation keeps automated tests deterministic while preserving registry-backed production behavior.

---

# 28. Production Model Selection

The serving layer does not independently select a model according to arbitrary performance heuristics.

Production selection is controlled through the MLflow alias:

```text
@production
```

The promotion process assigns this alias only after the lifecycle gates are satisfied.

Therefore:

```text
Registry version ≠ production
```

and:

```text
Best-looking candidate ≠ automatically deployed candidate
```

The alias is the authoritative production selection mechanism.

---

# 29. Reproducibility

The ML pipeline is designed so that model-development steps can be reproduced from repository-controlled inputs and scripts.

Important ML components include:

```text
ml/features/
ml/training/
ml/evaluation/
ml/monitoring/
ml/lifecycle/
```

and lifecycle scripts include:

```text
scripts/phase1_build_features.py
scripts/phase1_train.py
scripts/simulate_production_data.py
scripts/retrain_candidate.py
scripts/promote_model.py
scripts/rollback_model.py
```

Experiment results and model artifacts are kept separate from application source code.

---

# 30. Testing Strategy

The ML implementation is covered by automated tests.

Testing covers:

* data validation
* feature construction
* model behavior
* inference behavior
* retraining eligibility
* production-data simulation
* lifecycle behavior
* monitoring-related logic

The final project verification produced:

```text
64 passed, 2 warnings
```

for the Python test suite.

Ruff verification also completed successfully:

```text
All checks passed!
```

The broader application verification additionally passed:

```text
API typecheck
Web lint
Web production build
```

---

# 31. Current Final ML State

The final ML state is intentionally explicit.

## Historical learned models

The original registered learned models remain available:

```text
v1 — Ridge
v2 — Random Forest
v3 — HistGradientBoosting
```

## Phase 6 candidates

The retraining candidates are:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

All Phase 6 candidates were rejected by the persistence-baseline gate.

## Production alias

```text
@production
```

currently has:

```text
no learned model assigned
```

## Operational serving

The platform can therefore operate using:

```text
persistence baseline
```

rather than falsely representing an unqualified learned model as production.

---

# 32. Why the Learned Model Was Not Forced Into Production

The final ML architecture intentionally preserves the baseline result even when it prevents a visually convenient lifecycle demonstration.

The persistence strategy remains a valid operational reference.

If a candidate cannot beat the required baseline on the designated validation metric, the candidate is rejected.

The system does not:

* modify the simulator solely to make a learned model win
* modify the promotion threshold to force deployment
* assign a production alias without passing the gate
* fabricate rollback history
* label a rejected model as production
* equate drift with automatic retraining

This is a deliberate property of the ML governance design.

---

# 33. Final ML Lifecycle

The implemented lifecycle is:

```text
NEW DATA
   ↓
DATA VALIDATION
   ↓
MONITORING
   ↓
POSSIBLE PERFORMANCE DEGRADATION
   ↓
RETRAINING ELIGIBILITY
   ↓
CANDIDATE TRAINING
   ↓
EXPERIMENT TRACKING
   ↓
MODEL REGISTRATION
   ↓
CANDIDATE EVALUATION
   ↓
COMPARE WITH PERSISTENCE BASELINE
   ↓
COMPARE WITH CURRENT PRODUCTION
   ↓
PROMOTION DECISION
   ├───────────────┐
   ↓               ↓
REJECT          PROMOTE
   │               │
   │               ↓
   │        NEW PRODUCTION
   │               │
   └──────→ INFERENCE
                   ↓
              MONITORING
                   ↓
          FUTURE EVALUATION
```

When no learned model satisfies the production gates:

```text
REJECT
   ↓
KEEP EXISTING PRODUCTION STATE
   ↓
CONTINUE BASELINE SERVING
```

This is the final intended behavior.

---

# 34. ML Design Principles

The final ML implementation follows these principles:

### 34.1 Baseline First

A learned model must demonstrate value over a simple operational baseline.

### 34.2 Reproducibility

Training, evaluation, and lifecycle decisions are implemented through repository-controlled code and tracked experiments.

### 34.3 Explicit Model Governance

Registration, evaluation, promotion, rejection, and rollback are separate lifecycle states.

### 34.4 Candidate Isolation

Retraining cannot silently replace the production model.

### 34.5 Monitoring Before Retraining

Monitoring provides evidence for lifecycle decisions but does not automatically retrain the system.

### 34.6 No Forced Promotion

A model is promoted only when the defined evaluation gates are satisfied.

### 34.7 Honest Production State

The production alias reflects the actual state of the system.

### 34.8 Safe Fallback

When no learned model qualifies for production, the persistence strategy remains available as the serving baseline.

### 34.9 CPU-First Engineering

The ML stack uses classical machine-learning methods suitable for normal laptop execution and does not depend on GPUs, large language models, transformers, or autonomous agents.

### 34.10 Operational Separation

The ML system is designed as an MLOps lifecycle rather than as a single model-training artifact.

---

# 35. Final Scope

The machine-learning component of the Building & Energy Intelligence Platform is complete at the implemented project scope.

It provides:

```text
✓ deterministic feature engineering
✓ temporal forecasting
✓ multiple learned model families
✓ explicit forecasting baselines
✓ multi-metric evaluation
✓ building-level evaluation
✓ MLflow experiment tracking
✓ MLflow model registry
✓ model signatures
✓ production alias management
✓ candidate model isolation
✓ retraining eligibility logic
✓ controlled production-data simulation
✓ candidate retraining
✓ baseline promotion gate
✓ rejection tracking
✓ rollback mechanism
✓ FastAPI inference boundary
✓ baseline serving fallback
✓ monitoring integration
✓ automated ML tests
✓ reproducible lifecycle scripts
```

It intentionally does not claim capabilities that are outside the implemented system, including:

```text
✗ live external building telemetry
✗ autonomous retraining
✗ automatic promotion
✗ guaranteed learned-model superiority
✗ fabricated production deployment
✗ real-world operational energy savings claims
```

The final ML system therefore represents a complete, controlled forecasting and MLOps lifecycle in which model quality, lifecycle state, and production status remain explicitly distinguishable.