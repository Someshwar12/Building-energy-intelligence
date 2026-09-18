# Project Phases

This document is the final phase record for the Building & Energy Intelligence Platform.

The project was developed as a staged machine-learning and software-engineering system. Each phase added a distinct capability while preserving the interfaces, contracts, evaluation principles, and engineering decisions established previously.

All planned implementation phases are complete.

There is no Phase 7.

The final project progression is:

```text
Phase 0 — Project Foundation
        ↓
Phase 1 — Data, Features & ML Baseline
        ↓
Phase 2 — ML Inference Service
        ↓
Phase 3 — Application Platform
        ↓
Phase 4 — MLOps & Model Lifecycle
        ↓
Phase 5 — Testing, CI & Observability
        ↓
Phase 6 — Controlled Retraining & Final Lifecycle
````

The final system therefore covers:

```text
Data
  ↓
Validation
  ↓
Feature Engineering
  ↓
Machine Learning
  ↓
Experiment Tracking
  ↓
Model Registry
  ↓
Controlled Evaluation
  ↓
Inference Service
  ↓
Application Platform
  ↓
Monitoring
  ↓
Drift / Performance Detection
  ↓
Retraining Eligibility
  ↓
Candidate Retraining
  ↓
Candidate Evaluation
  ↓
Promotion / Rejection
  ↓
Rollback Capability
```

The project remains intentionally local, CPU-first, reproducible, and laptop-runnable. It demonstrates an end-to-end ML/MLOps lifecycle rather than a production-scale cloud deployment.

---

# Phase 0 — Project Foundation

## Status

**Complete**

## Objective

Establish the repository, development environment, dataset, project structure, development conventions, and initial data understanding required for the subsequent machine-learning and application phases.

## Main Work

* Project repository created.
* Git and GitHub workflow established.
* Python virtual environment established.
* BDG2 dataset acquired.
* Raw data organized.
* Initial dataset inspection performed.
* Project directory structure established.
* Development conventions established.
* Initial documentation structure established.

## Outcome

Phase 0 established the reproducible project foundation used by all subsequent phases.

---

# Phase 1 — Data, Features & ML Baseline

## Status

**Complete**

## Objective

Build the first reproducible energy-forecasting pipeline using the Building Data Genome Project 2 dataset and establish a defensible machine-learning benchmark.

## Dataset

The project uses the Building Data Genome Project 2 (BDG2) dataset.

The selected development population contains:

* 12 buildings.
* 17,544 hourly observations per building.
* 210,528 processed rows in total.
* Electricity consumption.
* Building metadata.
* Weather information.
* Historical observations covering 2016-01-01 through 2017-12-31.

The canonical processed dataset is:

```text
data/processed/phase1_features.parquet
```

The 12-building population defines the historical development and evaluation scope. It is not equivalent to runtime monitoring observations or simulated production observations.

## Data Pipeline

```text
Raw BDG2 Data
      ↓
Data Validation
      ↓
Cleaning / Alignment
      ↓
Feature Engineering
      ↓
Processed Feature Dataset
```

## Feature Engineering

The feature pipeline includes:

* Building identifiers.
* Site information.
* Primary-use metadata.
* Building area information.
* Weather variables.
* Calendar features.
* Historical energy features.
* Lag features.
* Rolling statistics.
* Heating degree-hour features.
* Cooling degree-hour features.

The prediction target is:

```text
target_next_hour_kwh
```

representing next-hour electricity consumption.

## Models and Baselines

The initial evaluation included:

* Persistence baseline.
* Previous-day baseline.
* Previous-week baseline.
* Ridge Regression.
* Random Forest.
* HistGradientBoosting.

The persistence baseline established a strong reference point.

Among the learned models in the original Phase 1 evaluation, Random Forest produced the strongest learned-model result under the validation macro-building NMAE criterion.

The project deliberately retains the distinction between:

```text
Operational reference:
Persistence

Learned models:
Ridge
Random Forest
HistGradientBoosting
```

The learned models are not automatically considered superior to the persistence strategy merely because they are more complex.

## Phase 1 Outcome

Phase 1 established:

* Reproducible data preparation.
* Feature engineering.
* Train/validation/test evaluation.
* Baseline comparison.
* Building-aware error analysis.
* ML artifacts.
* Initial model input/output contracts.

---

# Phase 2 — ML Inference Service

## Status

**Complete**

## Objective

Turn the Phase 1 forecasting system into a standalone, validated inference service.

## Architecture

```text
Client
  ↓
FastAPI
  ↓
Request Validation
  ↓
Feature Construction
  ↓
ML Model / Persistence Baseline
  ↓
Prediction Response
```

## Main Work

* FastAPI inference service created.
* Model loading implemented.
* Model artifact validation implemented.
* Request schemas implemented.
* Prediction response schema implemented.
* Feature parity with Phase 1 maintained.
* 168-hour historical context requirement enforced.
* Health endpoint implemented.
* Readiness endpoint implemented.
* Prediction endpoint implemented.
* Structured error handling implemented.
* Logging implemented.
* Unit tests implemented.

## Service

```text
apps/model_service/
```

Primary inference endpoint:

```text
POST /predict
```

Health and readiness endpoints:

```text
GET /health
GET /ready
```

## Prediction Contract

A learned-model prediction requires the historical context needed to construct the same feature representation used during training.

The request contains:

```text
168 hours of historical observations
        +
building metadata
        +
weather context
        +
target timestamp
        ↓
Feature Construction
        ↓
Model Inference
        ↓
Prediction
```

The service also supports a persistence baseline serving mode.

When the system is operating in baseline mode, the next-hour prediction is the most recently observed energy value supplied in the request history.

## Outcome

Phase 2 transformed the project from an ML experiment into a standalone ML inference service with an explicit API boundary.

---

# Phase 3 — Application Platform

## Status

**Complete**

## Objective

Build a functional web application around the ML inference service so that the forecasting system operates as an application rather than exposing the ML service directly to users.

## Architecture

```text
Next.js / React
      ↓
Node.js / Express
      ↓
FastAPI ML Service
      ↓
ML Model / Persistence Baseline
```

## Frontend Stack

The frontend uses:

* Next.js.
* React.
* TypeScript.
* Tailwind CSS.
* Recharts.

## Application Capabilities

The application provides:

* Overview.
* Building listing.
* Building detail pages.
* Building metadata.
* Historical consumption analysis.
* Forecast views.
* Consumption views.
* Anomaly analysis.
* Model Lab.
* Monitoring.
* Loading states.
* Empty states.
* Error states.
* Responsive layouts.

## Application API

The Node.js/Express application API separates application concerns from ML inference concerns.

Responsibilities include:

* Building discovery.
* Building metadata retrieval.
* Historical consumption retrieval.
* Prediction-context preparation.
* Communication with the ML service.
* Anomaly analysis.
* Model-lifecycle data access.
* Application-level error handling.

## Forecast Flow

```text
Building Detail Page
      ↓
Next.js Client
      ↓
Express Forecast Route
      ↓
Prediction Context
      ↓
FastAPI /predict
      ↓
ML Inference / Baseline
      ↓
Forecast Response
      ↓
Express
      ↓
Next.js Forecast UI
```

## Building-Level Workflow

The building detail experience combines:

```text
Consumption Analysis
        +
Next-Hour Forecast
        +
Building Profile
```

## Final Application Routes

```text
/
/anomalies
/buildings
/buildings/[buildingId]
/consumption
/forecasts
/model-lab
/monitoring
```

## Outcome

Phase 3 established the integrated application platform connecting the frontend, application API, ML inference service, and forecasting system.

---

# Phase 4 — MLOps & Model Lifecycle

## Status

**Complete**

## Objective

Introduce reproducible local infrastructure, experiment tracking, model registration, model signatures, controlled promotion, and safe baseline serving.

## Containerized Architecture

The project was containerized into four local services:

```text
Web
  ↓
Application API
  ↓
Model Service
  ↓
MLflow
```

Services:

```text
Web              : 3000
Application API  : 4000
Model Service    : 8000
MLflow           : 5000
```

Docker Compose provides the local service network and persistent MLflow storage.

## Experiment Tracking

MLflow is used for experiment tracking.

The primary Phase 1 experiment is:

```text
building-energy-phase1
```

Training runs record relevant experiment information including:

* Model parameters.
* Validation metrics.
* Test metrics.
* Dataset/reference information.
* Configuration.
* Git information where available.
* Model artifacts.
* Model signatures.
* Model-family metadata.
* Validation status.

## Model Registry

The registered model is:

```text
building-energy-forecast
```

The historical Phase 1 registry versions are:

```text
v1 — Ridge
v2 — Random Forest
v3 — HistGradientBoosting
```

All three registered versions are READY.

Version v2 contains explicit rejection metadata documenting its failure against the persistence baseline guard.

## Promotion Policy

The system does not promote a learned model merely because it is the strongest learned model.

The lifecycle is:

```text
Training
   ↓
MLflow Experiment
   ↓
Evaluation
   ↓
Learned Model Comparison
   ↓
Persistence Baseline Comparison
   ↓
Baseline Guard
   ↓
Promotion Decision
```

The learned-model selection criterion is:

```text
validation_macro_building_nmae
```

The baseline guard compares the learned candidate against the persistence benchmark.

A learned model therefore requires evidence of value against the simple operational baseline before becoming learned production.

## Production State

The final Phase 4 state was:

```text
Learned production model:
None

Operational serving strategy:
Persistence baseline
```

No learned model was artificially assigned the `@production` alias.

This is intentional and remains part of the final system architecture.

## Baseline-Safe Serving

The model service supports:

```text
Learned mode
Baseline mode
```

When a valid learned production alias does not exist, the service falls back to persistence.

The final runtime baseline identity is:

```text
model_name    = persistence
model_version = baseline
serving_mode  = baseline
```

## Model Signatures

The registered model versions were verified against the Docker-hosted MLflow server.

The signatures describe the expected forecasting feature contract, including:

* Building identifiers.
* Site information.
* Primary-use information.
* Building-area information.
* Weather variables.
* Calendar features.
* Historical energy features.
* Lag features.
* Rolling features.
* Heating degree-hour features.
* Cooling degree-hour features.

The model output is a numeric prediction vector.

## Model Lab

The Model Lab application surface exposes model-lifecycle information including:

* Registered model versions.
* Model runs.
* Model parameters.
* Model metrics.
* Lifecycle metadata.
* Evaluation metadata.
* Baseline information.
* Registry state.
* Serving state.

Model Lab is an observability and lifecycle surface. It does not allow arbitrary user-selected production model deployment.

## Outcome

Phase 4 established:

```text
Data
  ↓
Feature Engineering
  ↓
Training
  ↓
MLflow Experiment
  ↓
Model Registry
  ↓
Evaluation
  ↓
Baseline Guard
  ↓
Controlled Serving
```

The project gained reproducible containerized execution, MLflow tracking, registered versions, model signatures, controlled promotion logic, baseline-aware rejection, and safe fallback serving.

---

# Phase 5 — Testing, CI & Observability

## Status

**Complete**

## Objective

Make the forecasting platform testable, continuously verifiable, observable, and capable of detecting data, service, drift, and performance degradation.

Phase 5 intentionally established the evidence layer required for controlled retraining rather than performing automatic retraining.

## Phase 5 Architecture

```text
Browser
   ↓
Next.js / React
   ↓
Node.js / Express
   ↓
FastAPI ML Service
   ↓
Model / Persistence Baseline
   ↓
Prediction
   ↓
┌─────────────────────────────────────────┐
│              Observability              │
│                                         │
│ Data Quality                            │
│ Feature Drift                           │
│ Prediction Monitoring                   │
│ Model Performance                       │
│ Service Health                          │
│ Sustained Degradation                   │
└─────────────────────────────────────────┘
   ↓
Monitoring API
   ↓
Monitoring Dashboard
```

Testing and CI operate alongside the runtime system:

```text
Source Change
     ↓
Automated Tests
     ↓
Static Analysis
     ↓
Type Checking
     ↓
Application Builds
     ↓
CI Verification
```

---

# Phase 5 Batch 1 — Testing Foundation

## Status

**Complete**

## Main Work

Automated tests were established around:

* Data validation.
* Feature engineering.
* Lag correctness.
* Rolling-window correctness.
* Future-leakage prevention.
* Feature schemas.
* Model behaviour.
* Prediction behaviour.
* Inference contracts.
* Baseline serving.
* API validation.
* Monitoring logic.

The tests cover:

```text
Data
  ↓
Features
  ↓
Model
  ↓
Inference API
  ↓
Monitoring
```

The inference service is tested for:

* Valid prediction requests.
* Invalid requests.
* Insufficient history.
* Duplicate timestamps.
* Invalid energy values.
* Invalid request fields.
* Health.
* Readiness.
* Prediction behaviour.

## Outcome

The project gained a repeatable automated verification layer.

---

# Phase 5 Batch 2 — Service & Integration Verification

## Status

**Complete**

## Main Work

Integration coverage was established for:

* Model-service behaviour.
* Prediction paths.
* Monitoring state.
* Model Lab.
* Application API.
* Anomaly functionality.
* Application-level data access.

The major integration path is:

```text
Frontend
   ↓
Express API
   ↓
FastAPI
   ↓
ML / Baseline
   ↓
Prediction
   ↓
Monitoring
```

## Outcome

The system was verified as an integrated application rather than only as isolated components.

---

# Phase 5 Batch 3 — Continuous Integration

## Status

**Complete**

## CI Checks

The core CI verification layers include:

```text
Python
├── pytest
└── Ruff

Application API
├── lint
├── typecheck
└── build

Web
├── lint
└── build
```

These checks are intended to detect:

* Test failures.
* Python lint violations.
* API lint violations.
* Type errors.
* Application build failures.
* Frontend lint violations.
* Frontend build failures.

## CI Philosophy

Fast blocking checks are separated from expensive lifecycle or infrastructure operations.

The project does not require:

* Full retraining on every commit.
* Large historical evaluation on every commit.
* Full Docker rebuilds on every source change.

## Outcome

Phase 5 established an automated engineering-quality gate.

---

# Phase 5 Batch 4 — Monitoring Foundation

## Status

**Complete**

## Prediction Monitoring

Prediction events record information including:

* Building ID.
* Timestamp.
* Prediction.
* Persistence baseline.
* Model name.
* Model version.
* Serving mode.

Runtime monitoring state is bounded to:

```text
1000 observations
```

This keeps local runtime memory predictable.

## Monitoring Observation Semantics

A monitoring observation represents a prediction event.

For example:

```text
3 monitoring observations
```

means:

```text
3 prediction events recorded by the running monitoring state
```

It does not mean:

```text
3 buildings
```

and it does not mean:

```text
3 historical dataset rows
```

The historical development dataset contains 12 buildings, while an individual prediction request uses 168 historical hourly observations. These are separate concepts.

## Service Health

The monitoring layer observes:

* Availability.
* Request count.
* Error count.
* Latency.
* Health state.
* Readiness state.
* Dependency status.

## Outcome

The running system gained an operational monitoring foundation.

---

# Phase 5 Batch 5 — Data Drift

## Status

**Complete**

## Objective

Detect meaningful changes in incoming feature distributions relative to a reference profile.

## Drift Method

The current implementation uses Population Stability Index (PSI).

```text
Reference Distribution
        +
Current Distribution
        ↓
PSI
        ↓
Drift Status
```

## Current Thresholds

```text
PSI < 0.10
    → healthy

0.10 ≤ PSI < 0.25
    → warning

PSI ≥ 0.25
    → critical
```

Minimum current sample count:

```text
30 observations
```

If fewer than 30 observations are available:

```text
insufficient_data
```

is returned instead of manufacturing a drift decision.

## Reference Profile

The reference profile is:

```text
configs/monitoring_reference.json
```

The system distinguishes:

```text
No measurable drift
```

from:

```text
Reference unavailable
```

## Monitored Feature Families

The drift system can monitor:

* Building characteristics.
* Calendar features.
* Historical energy features.
* Rolling energy features.
* Weather variables.
* Temperature-derived features.

## Optional Weather Handling

Optional weather fields are handled safely.

Missing optional weather values do not cause monitoring instrumentation to break an otherwise valid prediction request.

## Outcome

The system gained explicit feature-distribution drift detection with sample-size safeguards and severity thresholds.

---

# Phase 5 Batch 6 — Monitoring UI

## Status

**Complete**

## Monitoring Dashboard

The Monitoring page exposes:

* Serving mode.
* Current model identity.
* Prediction observations.
* Data-quality state.
* Drift state.
* Performance state.
* Service health.
* Recent monitoring signals.
* Performance trends.
* Building-level information where available.

## Design Principle

Monitoring is an observability surface.

It does not:

* Automatically retrain models.
* Automatically promote models.
* Replace MLflow.
* Override the promotion guard.

## Outcome

Runtime ML and service health information became accessible through the application.

---

# Phase 5 Batch 7 — Model Performance & Degradation Monitoring

## Status

**Complete**

## Objective

Track actual forecasting performance over time and detect sustained degradation.

## Prediction and Outcome Separation

A prediction is recorded when a prediction event occurs:

```text
Prediction
   ↓
Prediction Record
```

A performance observation requires the corresponding actual outcome:

```text
Prediction
   +
Actual Outcome
   ↓
Performance Observation
```

This prevents the system from evaluating a prediction before the actual value exists.

## Performance Metrics

The monitoring system calculates:

* MAE.
* RMSE.
* NMAE.
* Persistence MAE.
* Persistence RMSE.
* Persistence NMAE.
* Building-level metrics.
* Comparison against persistence.

## Building-Level Monitoring

Performance can be calculated:

```text
Globally
+
Per Building
```

This preserves the building-aware evaluation philosophy established in Phase 1.

## Performance Window

The default recent performance window is:

```text
30 observations
```

## Sustained Degradation

The system requires:

```text
30 observations per window
3 sustained windows
```

Therefore:

```text
30 × 3 = 90 outcome observations
```

are required before the default sustained-degradation decision can be evaluated.

A single poor window does not establish sustained degradation.

Until sufficient observations exist, the state may remain:

```text
insufficient_data
```

## Degradation Threshold

The default relative degradation threshold is:

```text
10%
```

The detector evaluates degradation across sustained windows rather than treating one isolated poor window as sufficient evidence.

## Baseline-Aware Performance

Persistence remains available alongside served-model predictions:

```text
Served Model
     vs.
Persistence Baseline
```

Both can be evaluated against the same actual outcomes.

## Outcome

Phase 5 established performance monitoring and sustained-degradation detection as the evidence layer required for controlled lifecycle action.

---

# Phase 5 Final Verification

## Status

**Complete**

The final verification performed before Phase 6 completion included:

```text
pytest -q
64 passed, 2 warnings

ruff check .
All checks passed!

API typecheck
Passed

Web lint
Passed

Web production build
Passed
```

The final application route set is:

```text
/
/anomalies
/buildings
/buildings/[buildingId]
/consumption
/forecasts
/model-lab
/monitoring
```

The containerized runtime was verified with:

```text
Web
API
Model Service
MLflow
```

The prediction path and monitoring functionality were verified in the containerized application.

## Runtime Stability Fix

During integration verification, an optional weather field could contain `None`.

Monitoring instrumentation initially attempted to convert the missing value directly to a float, causing a valid prediction request to fail.

The monitoring feature extraction was corrected so optional weather fields are only processed when present.

The result is that observability instrumentation no longer breaks valid inference requests.

## Sustained-Degradation Contract Fix

An intermediate implementation allowed a single 30-observation window to produce a degraded decision.

The contract was corrected to require:

```text
90 outcome observations
=
3 × 30-observation windows
```

The relevant tests were updated and the final test suite passed.

---

# Phase 6 — Controlled Retraining & Final Lifecycle

## Status

**Complete**

## Objective

Complete the ML lifecycle by introducing simulated production-data arrival, controlled distribution shift, explicit retraining eligibility, candidate retraining, experiment tracking, candidate evaluation, promotion/rejection controls, and rollback capability.

Phase 6 is the final implementation phase.

There is no Phase 7.

## Final Lifecycle

The completed lifecycle is:

```text
NEW DATA
   ↓
VALIDATION
   ↓
MONITORING
   ↓
POSSIBLE DEGRADATION
   ↓
RETRAINING ELIGIBILITY
   ↓
CANDIDATE TRAINING
   ↓
EXPERIMENT TRACKING
   ↓
CANDIDATE EVALUATION
   ↓
COMPARE WITH PRODUCTION
   ↓
COMPARE WITH PERSISTENCE
   ↓
PROMOTION DECISION
   ├── REJECT
   └── PROMOTE
          ↓
     NEW PRODUCTION MODEL
          ↓
       INFERENCE
          ↓
      MONITORING
```

The implemented lifecycle is controlled rather than automatic.

---

# Phase 6 Batch 1 — Retraining Eligibility

## Status

**Complete**

## Objective

Convert Phase 5 monitoring evidence into an explicit retraining-eligibility decision.

Retraining eligibility does not itself perform training.

The eligibility contract requires evidence from multiple signals:

```text
Sufficient Observations
        +
Sustained Performance Degradation
        +
Baseline Comparison
        +
Data Quality Not Critical
        +
Service State Acceptable
        +
Supporting Drift Evidence
        ↓
Retraining Eligibility Decision
```

Drift alone does not trigger retraining.

## Eligibility Evidence

The eligibility decision records:

* Current model identity.
* Model version.
* Serving mode.
* Sample count.
* Required sample count.
* Sustained degradation state.
* Current model NMAE.
* Persistence NMAE.
* Baseline comparison availability.
* Whether the learned model beats persistence.
* Drift status.
* Data-quality status.
* Service status.
* Positive reasons.
* Blocking reasons.

Possible final states include:

```text
retraining_eligible
not_eligible
```

## Outcome

The project gained an explicit lifecycle gate between monitoring evidence and candidate retraining.

---

# Phase 6 Batch 2 — Simulated Production Data

## Status

**Complete**

## Objective

Create deterministic local production-like data so that the complete monitoring and retraining lifecycle can be demonstrated without requiring a live telemetry infrastructure.

The simulation uses the processed Phase 1 dataset as its source.

The production simulation selects:

```text
168 observations × 12 buildings
=
2016 observations
```

Two scenarios are generated:

```text
Normal Production
Shifted Production
```

## Normal Scenario

The normal scenario preserves the underlying target behaviour while applying only small deterministic weather perturbations.

Output:

```text
data/interim/production/normal_production.parquet
```

## Shifted Scenario

The shifted scenario applies a controlled distribution shift to incoming conditions.

The implemented shift includes:

* Air temperature shift.
* Dew temperature shift.
* Wind-speed scaling.
* Target consumption shift.
* Deterministic small noise.

Output:

```text
data/interim/production/shifted_production.parquet
```

The simulator uses a deterministic seed so that the demonstration is reproducible.

## Outcome

The project gained reproducible production-like data for demonstrating drift, performance changes, and candidate retraining without pretending that the historical dataset is a live telemetry system.

---

# Phase 6 Batch 3 — Candidate Retraining

## Status

**Complete**

## Objective

Train new models from the simulated production data while keeping them isolated from the current serving state.

The candidate training process uses:

```text
data/interim/production/
```

with the normal or shifted scenario selected explicitly.

## Candidate Experiment

A separate MLflow experiment is used:

```text
building-energy-retraining
```

The registered model remains:

```text
building-energy-forecast
```

The candidate models generated from the shifted scenario were:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

## Candidate Lifecycle

Candidate training records:

* Training run.
* Dataset information.
* Model family.
* Model artifact.
* Model signature.
* Candidate metadata.
* Validation metadata.
* Source simulation mode.
* Lifecycle stage.

Candidate models do not receive the production alias during training.

## Candidate Isolation

The fundamental rule is:

```text
Candidate
   ≠
Production
```

A newly trained candidate cannot replace the serving model merely because training completed successfully.

## Outcome

The project gained reproducible candidate-model generation without directly affecting production serving.

---

# Phase 6 Batch 4 — Candidate Evaluation & Promotion/Rejection

## Status

**Complete**

## Objective

Evaluate retrained candidates against the current serving strategy and the persistence baseline before making a lifecycle decision.

The evaluation was performed against the shifted simulated production scenario.

## Candidate Results

The resulting candidate NMAE values were:

```text
v4 — Ridge
candidate NMAE = 13.008031

v5 — Random Forest
candidate NMAE = 9.466449

v6 — HistGradientBoosting
candidate NMAE = 2.904410
```

The persistence baseline on the same evaluation data was:

```text
persistence NMAE = 0.219467
```

Therefore, none of the three candidates beat persistence on the candidate evaluation.

## Lifecycle Decision

The final decision was:

```text
v4 — REJECTED
v5 — REJECTED
v6 — REJECTED
```

The rejection reason was that the candidate did not beat the persistence baseline.

No learned production model was created.

## Important Lifecycle Principle

The system does not force promotion simply because a candidate was retrained.

The actual lifecycle outcome is allowed to be:

```text
Candidate
   ↓
Evaluation
   ↓
Reject
   ↓
Keep Current Serving Strategy
```

This is a valid and intentional final outcome.

## Final Production State

After candidate evaluation:

```text
Learned production model:
None

Production alias:
None

Operational serving strategy:
Persistence baseline
```

The project therefore demonstrates both candidate creation and controlled rejection.

---

# Phase 6 Batch 5 — Rollback Capability

## Status

**Complete**

## Objective

Provide an explicit operational mechanism for restoring a known registered model version if a learned production model exists and requires rollback.

The rollback mechanism operates through the MLflow production alias.

Conceptually:

```text
Current Production
       ↓
Operational Problem
       ↓
Select Known Version
       ↓
Validate Target
       ↓
Move @production
       ↓
Record Rollback Metadata
```

Rollback metadata includes:

* Rollback status.
* Rollback timestamp.
* Previous production version.
* Rollback reason.
* Restored lifecycle state.

## Safety Behaviour

The rollback mechanism refuses to fabricate a rollback when no learned production model exists.

During final validation, attempting:

```text
python scripts/rollback_model.py --to-version 1
```

correctly produced the safety error indicating that no learned production model currently existed.

This is expected because the final lifecycle never promoted a learned candidate.

The rollback mechanism is therefore implemented and safety-validated without artificially creating a production state solely for demonstration.

---

# Phase 6 Batch 6 — Lifecycle API & Application Observability

## Status

**Complete**

## Objective

Expose the completed ML lifecycle through the existing model-service and application observability surfaces.

The model service provides lifecycle and monitoring endpoints including:

```text
GET /model-lab/summary
GET /model-lab/versions
GET /model-lab/runs

GET /monitoring/summary
GET /monitoring/drift
GET /monitoring/performance
GET /monitoring/outcomes

GET /health
GET /ready

POST /predict
```

## Model Lab

The final Model Lab exposes:

* Model versions.
* Model families.
* Runs.
* Registry state.
* Lifecycle state.
* Evaluation metadata.
* Promotion metadata.
* Rejection metadata.
* Baseline information.
* Serving state.

The Model Lab makes the lifecycle visible without introducing arbitrary user-controlled production selection.

## Monitoring

The final Monitoring surface exposes:

* Serving mode.
* Model identity.
* Runtime health.
* Prediction monitoring.
* Data quality.
* Feature drift.
* Performance.
* Degradation state.
* Diagnostic information.

## Outcome

The application exposes the ML lifecycle and monitoring system as first-class product functionality.

---

# Phase 6 Batch 7 — Final Verification & Publication Readiness

## Status

**Complete**

## Final Automated Verification

The final Python test suite passed:

```text
64 passed
2 warnings
```

Ruff passed:

```text
All checks passed!
```

The application API typecheck passed.

The web lint passed.

The web production build passed.

The final application route set is:

```text
/
/anomalies
/buildings
/buildings/[buildingId]
/consumption
/forecasts
/model-lab
/monitoring
```

## Final Project Verification

The final implementation verifies:

```text
Data pipeline                         ✓
Feature engineering                  ✓
ML training                          ✓
Baseline evaluation                  ✓
MLflow experiment tracking           ✓
Model registry                       ✓
Model signatures                     ✓
Inference service                    ✓
Application API                      ✓
React / Next.js application          ✓
Docker Compose runtime               ✓
Automated tests                      ✓
CI verification                      ✓
Prediction monitoring                ✓
Data-quality monitoring              ✓
Feature drift detection              ✓
Performance monitoring               ✓
Sustained degradation detection      ✓
Retraining eligibility               ✓
Production-data simulation           ✓
Controlled distribution shift        ✓
Candidate retraining                 ✓
Candidate MLflow tracking             ✓
Candidate evaluation                 ✓
Persistence comparison               ✓
Promotion/rejection decision         ✓
Rollback mechanism                   ✓
Lifecycle observability              ✓
Model Lab                            ✓
Monitoring dashboard                 ✓
```

---

# Final Model Lifecycle State

The final MLflow registry contains the original Phase 1 learned models and the Phase 6 retraining candidates.

Historical learned models:

```text
v1 — Ridge
v2 — Random Forest
v3 — HistGradientBoosting
```

Phase 6 retraining candidates:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

The Phase 6 candidates were evaluated and rejected because none beat the persistence baseline on the shifted production evaluation.

The final serving state is therefore:

```text
Production alias:
None

Serving mode:
baseline

Serving strategy:
Persistence

Model name:
persistence

Model version:
baseline
```

This state is intentional.

The project does not create a false learned production model simply to demonstrate a promotion event.

---

# Final System Architecture

The completed platform can be represented as:

```text
                         ┌───────────────────────┐
                         │       BDG2 Data       │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Validation & Features │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Baselines + ML Models │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │   MLflow Experiments  │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │    Model Registry     │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Evaluation + Guards   │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Controlled Serving    │
                         │ Learned / Baseline    │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ FastAPI Inference     │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Application Platform  │
                         │ Next.js + Express     │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Prediction Monitoring │
                         └───────────┬───────────┘
                                     ↓
              ┌──────────────────────┼──────────────────────┐
              ↓                      ↓                      ↓
       Data Quality            Feature Drift          Performance
              │                      │                      │
              └──────────────────────┼──────────────────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Degradation Detection │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Retraining Eligibility│
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Candidate Training    │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Candidate Evaluation  │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Promotion / Rejection │
                         └───────────┬───────────┘
                                     ↓
                         ┌───────────────────────┐
                         │ Production / Rollback │
                         └───────────────────────┘
```

---

# Final Lifecycle Demonstration

The complete project can demonstrate the following sequence:

```text
1. Normal system
        ↓
2. Prediction
        ↓
3. Anomaly detection
        ↓
4. Model / serving health
        ↓
5. New simulated production data
        ↓
6. Controlled distribution shift
        ↓
7. Drift detection
        ↓
8. Performance evaluation
        ↓
9. Sustained degradation evidence
        ↓
10. Retraining eligibility
        ↓
11. Candidate training
        ↓
12. MLflow experiment tracking
        ↓
13. Candidate registration
        ↓
14. Candidate evaluation
        ↓
15. Persistence baseline comparison
        ↓
16. Promotion / rejection decision
        ↓
17. If accepted: production alias update
        ↓
18. If rejected: current serving strategy retained
        ↓
19. Inference
        ↓
20. Monitoring
        ↓
21. Future lifecycle decision
```

The actual Phase 6 demonstration followed the rejection path because the persistence baseline remained substantially stronger than the retrained candidates on the shifted evaluation scenario.

This is an intentional lifecycle result rather than an incomplete implementation.

---

# Final Engineering Principles

## 1. Build incrementally

Each phase introduced one major engineering capability.

## 2. Preserve contracts

Later phases build on the interfaces established by earlier phases.

## 3. Validate before advancing

Every major phase was verified before becoming a dependency for subsequent work.

## 4. Establish baselines before complexity

A learned model must demonstrate measurable value against a simple reference.

## 5. Evaluation precedes production

A trained model is not automatically a production model.

## 6. Candidate and production remain separate

Candidate training cannot directly overwrite the serving state.

## 7. Monitoring and retraining are separate systems

Monitoring produces evidence.

Retraining consumes an explicit eligibility decision.

## 8. Drift does not automatically trigger retraining

Feature drift is supporting evidence, not an unconditional retraining command.

## 9. Sustained degradation matters

A single poor observation or single poor performance window is insufficient to establish sustained degradation.

## 10. Actual outcomes are required for performance measurement

Predictions are recorded immediately, but performance can only be evaluated after the corresponding actual outcome becomes available.

## 11. Persistence remains first-class

Persistence is used consistently as:

* Evaluation baseline.
* Promotion guard.
* Serving fallback.
* Performance reference.
* Retraining evaluation reference.

## 12. Failure states remain explicit

Examples include:

```text
rejected
insufficient_data
reference_unavailable
not_eligible
baseline serving
```

These are valid system states and are not hidden.

## 13. Do not force successful promotion

If every candidate fails evaluation, the existing serving strategy remains unchanged.

## 14. Rollback must be safe

Rollback operates only against an existing learned production state and a valid registered target.

## 15. Prefer reproducibility

Experiments, datasets, model versions, configurations, signatures, and lifecycle decisions should remain traceable.

## 16. Avoid unnecessary infrastructure complexity

The system is intentionally:

* CPU-first.
* Laptop-runnable.
* Locally deployable.
* Open-source oriented.
* Free to develop.
* Free from unnecessary GPU, LLM, agent, Kubernetes, and distributed infrastructure requirements.

---

# Final Project Status

All implementation phases are complete:

```text
Phase 0  ✓ Complete
Phase 1  ✓ Complete
Phase 2  ✓ Complete
Phase 3  ✓ Complete
Phase 4  ✓ Complete
Phase 5  ✓ Complete
Phase 6  ✓ Complete
```

There is no Phase 7.

There is no additional implementation phase required to complete the defined project lifecycle.

---

# Final System State

The final platform provides:

```text
Historical Data
      ↓
Validation
      ↓
Feature Engineering
      ↓
Baseline + ML Training
      ↓
MLflow Tracking
      ↓
Model Registry
      ↓
Evaluation
      ↓
Promotion Guard
      ↓
Controlled Serving
      ↓
FastAPI Inference
      ↓
Application Platform
      ↓
Prediction Monitoring
      ↓
Data Quality
      ↓
Feature Drift
      ↓
Performance Monitoring
      ↓
Sustained Degradation
      ↓
Retraining Eligibility
      ↓
Candidate Retraining
      ↓
MLflow Candidate Tracking
      ↓
Candidate Evaluation
      ↓
Persistence Comparison
      ↓
Promotion / Rejection
      ↓
Production Alias / Existing Serving Strategy
      ↓
Rollback Capability
      ↓
Continued Inference & Monitoring
```

The final operational serving state is:

```text
Serving mode:
baseline

Serving strategy:
Persistence

Learned production alias:
None
```

The final Phase 6 candidate state is:

```text
v4 — Ridge                    REJECTED
v5 — Random Forest            REJECTED
v6 — HistGradientBoosting     REJECTED
```

The candidates were rejected because none beat the persistence baseline on the controlled shifted-production evaluation.

The system therefore ends in a safe and internally consistent state:

```text
No learned candidate passed the promotion gate
                    ↓
No learned production alias
                    ↓
Persistence remains the serving strategy
                    ↓
Monitoring remains active
                    ↓
Future data could produce a new eligibility decision
```

No artificial promotion, forced model selection, or fabricated production state is introduced.

---

# Final Project Maturity

The completed project demonstrates the progression:

```text
Phase 0
Repository / Data Foundation
        ↓
Phase 1
Reproducible ML Experiment
        ↓
Phase 2
Standalone Inference Service
        ↓
Phase 3
Integrated Application
        ↓
Phase 4
Managed ML Lifecycle
        ↓
Phase 5
Tested + CI-Verified + Observable ML System
        ↓
Phase 6
Controlled Model Updating
```

The resulting system demonstrates not only model training, but the engineering surrounding an ML forecasting system:

```text
Data
+
Machine Learning
+
Software Engineering
+
API Design
+
Containerization
+
Experiment Tracking
+
Model Registry
+
Evaluation
+
Baseline Governance
+
Monitoring
+
Drift Detection
+
Performance Monitoring
+
Retraining Eligibility
+
Candidate Management
+
Promotion / Rejection
+
Rollback
+
Testing
+
CI
```

The project is complete within its defined scope.

Its final architecture intentionally demonstrates a controlled ML lifecycle rather than pretending to be a production-scale cloud platform.

The core engineering principle that governs the completed system is:

```text
Build
  ↓
Validate
  ↓
Measure
  ↓
Register
  ↓
Evaluate
  ↓
Promote Carefully
  ↓
Serve
  ↓
Monitor
  ↓
Detect Evidence of Degradation
  ↓
Establish Retraining Eligibility
  ↓
Train a Candidate
  ↓
Evaluate Again
  ↓
Promote or Reject
  ↓
Continue Monitoring
```

This is the final project phase structure and final lifecycle state.