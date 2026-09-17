# Project Phases

This project is developed as a staged machine-learning and software engineering system.

Each phase adds a distinct layer to the platform while preserving the interfaces, contracts, and decisions established in previous phases.

The overall progression is:

```text
Data
  ↓
Feature Engineering
  ↓
Machine Learning
  ↓
ML Inference Service
  ↓
Application Platform
  ↓
MLOps & Model Lifecycle
  ↓
Testing, CI & Observability
  ↓
Controlled Retraining
  ↓
Deployment
````

---

# Phase 0 — Project Foundation

## Status

**Complete**

## Objective

Establish the project repository, development environment, data source, project structure, and initial data understanding.

## Main Work

* Project repository created
* Python virtual environment established
* Git and GitHub workflow established
* BDG2 dataset acquired
* Raw data organized
* Initial dataset inspection performed
* Project directory structure established
* Development conventions established

## Output

A reproducible project foundation for the subsequent ML and application phases.

---

# Phase 1 — Data, Features & ML Baseline

## Status

**Complete**

## Objective

Build the first reproducible energy forecasting pipeline using the BDG2 dataset and establish a defensible ML benchmark.

## Dataset

The project uses the Building Data Genome Project 2 (BDG2) dataset.

The selected working subset contains:

* 12 buildings
* hourly observations
* electricity consumption
* building metadata
* weather information

The canonical processed dataset is:

```text
data/processed/phase1_features.parquet
```

The processed development dataset contains approximately:

```text
210,528 rows
12 buildings
```

The 12 buildings describe the development dataset scope. They are not equivalent to runtime monitoring observations.

## Data Pipeline

The phase established:

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

Features include:

* historical energy values
* lag features
* rolling mean features
* rolling maximum features
* weather variables
* building metadata
* calendar features
* heating degree hours
* cooling degree hours

The prediction target is:

```text
target_next_hour_kwh
```

representing next-hour electricity consumption.

## Models Evaluated

The initial benchmark included:

* Persistence baseline
* Previous-day baseline
* Previous-week baseline
* Ridge Regression
* Random Forest
* HistGradientBoosting

## Model Selection

The persistence strategy established a strong benchmark on the selected evaluation setup.

Among the learned models, Random Forest provided the strongest learned-model result under the current validation macro-building NMAE selection criterion.

The project therefore distinguishes:

```text
Baseline:
Persistence

Strongest evaluated learned candidate:
Random Forest
```

The initial Random Forest artifact is:

```text
models/random_forest_phase1.joblib
```

## Phase 1 Outcome

Phase 1 established:

* reproducible data preparation
* feature engineering
* train/validation/test evaluation
* baseline comparison
* model error analysis
* ML artifacts
* the initial ML input/output contract

---

# Phase 2 — ML Inference Service

## Status

**Complete**

## Objective

Turn the Phase 1 ML model into a standalone, validated inference service.

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
ML Model / Baseline
  ↓
Prediction Response
```

## Main Work

* FastAPI inference service created
* Model loading implemented
* Model artifact validation implemented
* Request schemas implemented
* Prediction response schema implemented
* Feature parity with Phase 1 maintained
* 168-hour historical context requirement enforced
* Health endpoint implemented
* Readiness endpoint implemented
* Prediction endpoint implemented
* Structured error handling implemented
* Logging implemented
* Unit tests implemented

## Service

The service is located at:

```text
apps/model_service/
```

The main inference endpoint is:

```text
POST /predict
```

## Prediction Contract

The inference service requires the historical context necessary to reproduce the feature construction.

The prediction workflow uses:

```text
168 hours of historical observations
        +
building metadata
        +
weather context
        +
target timestamp
        ↓
Feature construction
        ↓
Inference
```

## Validation

Phase 2 established a tested ML service boundary through:

* unit tests
* request validation tests
* model-loading tests
* inference tests
* API prediction verification
* Ruff validation

## Phase 2 Outcome

The project progressed from:

```text
ML experiment
```

to:

```text
Standalone ML inference service
```

This created the service boundary required by the application layer.

---

# Phase 3 — Application Platform

## Status

**Complete**

## Objective

Build a functional web application around the existing ML inference service.

The objective was to create a real application workflow rather than exposing the ML service directly to users.

## Architecture

```text
Next.js / React
      ↓
Node.js / Express
      ↓
FastAPI ML Service
      ↓
ML Model / Baseline
```

## Frontend

The frontend was implemented using:

* Next.js
* React
* TypeScript
* Tailwind CSS
* Recharts

The frontend provides:

* application overview
* building listing
* building detail pages
* building metadata
* historical consumption visualization
* forecast display
* anomaly analysis
* consumption analysis
* forecast views
* loading states
* empty states
* error states
* responsive layouts

## Application API

A Node.js/Express application API was introduced.

Its responsibilities include:

* building discovery
* building metadata retrieval
* historical consumption retrieval
* prediction context preparation
* communication with the ML service
* anomaly analysis
* model-lifecycle data access
* application-level error handling

The API separates application concerns from ML inference concerns.

## Historical Consumption

The application reads the canonical Phase 1 feature dataset and exposes building-level historical consumption through the application API.

The frontend renders the resulting observations using analytical chart components.

## Forecast Integration

The application connects the frontend to the ML inference service.

The complete flow is:

```text
Building Detail Page
      ↓
Next.js API Client
      ↓
Express Forecast Route
      ↓
Prediction Context
      ↓
FastAPI /predict
      ↓
ML Inference
      ↓
Forecast Response
      ↓
Express
      ↓
Next.js Forecast UI
```

## Building-Level Workflow

The building detail page combines:

```text
Consumption Analysis
        +
Next-hour Forecast
        +
Building Profile
```

The consumption and forecast views form the primary analytical workflow.

## Additional Application Views

The application also provides dedicated views for:

* Buildings
* Consumption
* Forecasts
* Anomalies
* Model Lab
* Monitoring

## Validation

Phase 3 established:

* Python test coverage
* Node API type checking
* Node API production build
* Next.js linting
* Next.js production build
* end-to-end prediction verification

## Scope Boundary

Phase 3 intentionally did not introduce:

* Docker
* MLflow
* experiment tracking
* model registry
* model promotion
* drift monitoring
* automated retraining
* CI/CD
* cloud deployment

These capabilities were reserved for later phases.

## Phase 3 Outcome

The project gained a functional application platform:

```text
Web Application
      ↓
Application API
      ↓
ML Inference Service
      ↓
Machine Learning
```

---

# Phase 4 — MLOps & Model Lifecycle

## Status

**Complete**

## Objective

Introduce reproducible local infrastructure and ML lifecycle management around the existing Building & Energy Intelligence forecasting system.

The phase moved the project from:

```text
A trained model artifact
```

to:

```text
A managed and evaluation-driven model lifecycle
```

## Main Work

### Containerization

The application was containerized into four local services:

* Next.js / React web application
* Node.js / Express application API
* FastAPI ML inference service
* MLflow tracking and model registry server

Docker Compose provides the local service network and persistent MLflow storage.

The services run locally on:

```text
Web              : 3000
Application API  : 4000
ML Service       : 8000
MLflow           : 5000
```

### Experiment Tracking

MLflow was introduced as the experiment tracking layer.

Training runs record information including:

* experiment configuration
* model parameters
* validation metrics
* test metrics
* dataset/reference information
* configuration
* Git commit information
* model artifacts
* model signatures
* model-family metadata
* validation status

The primary MLflow experiment is:

```text
building-energy-phase1
```

### Model Registry

The registered MLflow model is:

```text
building-energy-forecast
```

The current registry contains:

| Version | Model                | Lifecycle state |
| ------- | -------------------- | --------------- |
| v1      | Ridge                | Evaluated       |
| v2      | Random Forest        | Rejected        |
| v3      | HistGradientBoosting | Evaluated       |

All registered versions are in `READY` state.

Version v2 contains explicit rejection metadata documenting that it failed the baseline guard.

No learned model currently has the `@production` alias.

This is intentional.

### Evaluation-Driven Promotion

The promotion workflow does not automatically promote the best learned model.

The process is:

```text
Training
   ↓
MLflow Experiment
   ↓
Evaluation
   ↓
Select Best Learned Candidate
   ↓
Compare Against Persistence Baseline
   ↓
Baseline Guard
   ↓
┌───────────────────────┐
│                       │
▼                       ▼
Pass                    Fail
│                       │
▼                       ▼
@production             Reject Candidate
```

The current learned-model selection metric is:

```text
validation_macro_building_nmae
```

The candidate must also satisfy the baseline guard.

This prevents a learned model from being promoted simply because it performs better than other learned models.

### Current Promotion Result

The current evaluated registry state does not contain a learned production model.

The persistence baseline remains the operational serving strategy because no learned candidate passed the baseline guard.

Conceptually:

```text
Learned production model:
None

Operational serving strategy:
Persistence baseline
```

The system does not artificially assign a production alias merely to populate the registry.

### Baseline-Safe Serving

The model service supports two serving modes:

```text
Learned mode
Baseline mode
```

When no valid learned production model exists, the service serves the persistence baseline.

The current runtime state is:

```text
model_name    = persistence
model_version = baseline
serving_mode  = baseline
```

Persistence predicts the next-hour energy value using the most recent observed energy value from the supplied historical observations.

This allows the application to remain operational while preserving the evaluation and promotion policy.

### MLflow Model Signature Verification

Registered model versions were verified against the Docker-hosted MLflow server.

The registered models expose the expected forecasting feature contract, including:

* building identifiers and metadata
* site and primary-use information
* building area information
* weather variables
* calendar features
* historical energy lag features
* rolling energy statistics
* heating degree-hour features
* cooling degree-hour features

The model output is a numeric prediction vector.

### Model Service Integration

The model service obtains model lifecycle information through MLflow when operating in MLflow mode.

The application architecture therefore becomes:

```text
Next.js
   ↓
Node / Express
   ↓
FastAPI ML Service
   ↓
MLflow Model Registry
   ↓
Registered Model
```

If no learned production alias is available, the service falls back to the persistence baseline.

### Runtime Verification

The Docker Compose stack was successfully verified with all four services running:

```text
Web              : 3000
API              : 4000
Model Service    : 8000
MLflow           : 5000
```

The primary model-service endpoints are:

```text
GET /health
GET /ready
POST /predict
```

The readiness state exposes the active serving strategy.

A real prediction request was verified through the containerized inference path.

### Model Lab

A Model Lab interface was added as an application-level observability surface for the MLflow lifecycle.

It exposes:

* registered model versions
* model runs
* lifecycle metadata
* evaluation metadata
* baseline information
* serving state
* model metrics
* model parameters
* registry state

The Model Lab is a supporting observability surface for the model lifecycle.

## Phase 4 Outcome

Phase 4 established the project's local MLOps lifecycle:

```text
Data
  ↓
Feature Engineering
  ↓
Training
  ↓
MLflow Experiment
  ↓
Evaluation
  ↓
Model Registry
  ↓
Baseline Promotion Guard
  ↓
Controlled Lifecycle Decision
  ↓
Production / Baseline Serving
```

The system now has:

* reproducible containerized execution
* MLflow experiment tracking
* registered model versions
* model signatures
* evaluation metadata
* controlled promotion
* baseline-aware rejection
* safe baseline serving
* persistent local MLflow storage
* verified ML inference

## Deferred From Phase 4

The following capabilities were intentionally deferred:

* automated data-quality monitoring
* data drift detection
* prediction monitoring
* automated performance monitoring
* degradation detection
* automated retraining
* retraining eligibility
* cloud deployment
* Kubernetes
* large-scale distributed infrastructure
* large LLM or agent infrastructure

These capabilities are handled by later phases only where they provide a concrete engineering benefit.

---

# Phase 5 — Testing, CI & Observability

## Status

**Complete**

## Objective

Make the forecasting platform testable, continuously verifiable, observable, and capable of detecting data, model, and service degradation.

Phase 5 extends the system from:

```text
A working ML application
```

to:

```text
A monitored and automatically verified ML system
```

The phase does not introduce automatic retraining.

Instead, it establishes the evidence and lifecycle state required before controlled retraining can occur in Phase 6.

---

# Phase 5 Architecture

The resulting operational architecture is:

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
│             Observability               │
│                                         │
│ Data Quality                            │
│ Feature Drift                           │
│ Prediction Monitoring                   │
│ Model Performance                       │
│ Service Health                          │
│ Degradation Detection                   │
└─────────────────────────────────────────┘
   ↓
Monitoring API
   ↓
Monitoring Dashboard
```

Testing and CI operate alongside this runtime path:

```text
Source Changes
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

## Objective

Establish a reliable automated testing foundation for the ML and application layers.

## Main Work

Tests were organized around the major system boundaries:

* data validation
* feature engineering
* model behaviour
* inference
* API contracts
* monitoring logic

The test strategy covers:

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

## ML Testing

Coverage includes:

* feature construction
* lag correctness
* rolling-window correctness
* absence of future leakage
* feature schema
* insufficient historical context
* prediction existence
* finite predictions
* nonnegative predictions
* deterministic behaviour
* model identity
* baseline serving behaviour

## API Testing

The inference service is tested for:

* valid prediction requests
* invalid requests
* insufficient history
* duplicate timestamps
* invalid energy values
* invalid request fields
* health endpoint
* readiness endpoint
* prediction endpoint

## Outcome

The project gained a repeatable automated verification layer rather than relying only on manual prediction testing.

---

# Phase 5 Batch 2 — Service & Integration Verification

## Status

**Complete**

## Objective

Verify that the major services work together across their real application boundaries.

## Main Work

Integration coverage was added for:

* model-service behaviour
* prediction path
* monitoring state
* Model Lab
* application API
* anomaly functionality
* application-level data access

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

The system was verified as an integrated application rather than a collection of independently tested components.

---

# Phase 5 Batch 3 — CI

## Status

**Complete**

## Objective

Automatically verify core project correctness through CI.

## CI Checks

The project CI covers the core verification layers:

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

These checks are intended to block changes that introduce:

* failing tests
* Python lint violations
* API lint violations
* type errors
* application build failures
* frontend lint violations
* frontend build failures

## CI Philosophy

Not every expensive operation needs to run for every source change.

The project intentionally separates:

```text
Fast blocking checks
```

from:

```text
Long-running evaluation / infrastructure checks
```

Full retraining, large historical evaluation, and full Docker rebuilds are not required for every commit.

## Outcome

The project gained an automated engineering quality gate.

---

# Phase 5 Batch 4 — Monitoring Foundation

## Status

**Complete**

## Objective

Create the runtime monitoring state and expose the main health and prediction signals.

## Prediction Monitoring

Prediction records capture information such as:

* building ID
* timestamp
* prediction
* persistence baseline
* model name
* model version
* serving mode

The monitoring state is bounded to:

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

and does not mean:

```text
3 historical dataset rows
```

The project dataset contains:

```text
12 development buildings
```

while each prediction request uses:

```text
168 historical hourly observations
```

These represent separate concepts.

## Service Health

The monitoring layer observes:

* availability
* request count
* error count
* latency
* health state
* readiness state
* dependency status

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

The conceptual flow is:

```text
Reference Distribution
        +
Current Distribution
        ↓
PSI
        ↓
Drift Status
```

## Thresholds

The current thresholds are:

```text
PSI < 0.10
    → healthy

0.10 ≤ PSI < 0.25
    → warning

PSI ≥ 0.25
    → critical
```

The minimum current sample count is:

```text
30
```

If fewer than 30 current observations are available, the result is:

```text
insufficient_data
```

rather than a drift decision.

## Reference Profile

The reference profile is:

```text
configs/monitoring_reference.json
```

The monitoring system distinguishes between:

```text
No measurable drift
```

and:

```text
Reference unavailable
```

This prevents missing reference data from being incorrectly interpreted as a healthy distribution.

## Monitored Feature Families

The drift layer can monitor:

* building characteristics
* calendar features
* historical energy features
* rolling energy features
* weather variables
* temperature-derived features

## Optional Weather Handling

Optional weather fields are handled safely.

Missing optional weather values do not cause monitoring instrumentation to crash an otherwise valid prediction request.

This preserves the separation between:

```text
Prediction correctness
```

and:

```text
Optional monitoring signals
```

## Outcome

The system gained explicit feature-distribution drift detection with sample-size safeguards and severity thresholds.

---

# Phase 5 Batch 6 — Monitoring UI

## Status

**Complete**

## Objective

Expose runtime ML and service health information through the application.

## Monitoring Dashboard

The Monitoring page provides visibility into:

* serving mode
* current model identity
* prediction observations
* data-quality state
* drift state
* performance state
* service health
* recent monitoring signals
* performance trends
* building-level information where available

## Design Principle

The Monitoring page is an observability surface.

It does not:

* automatically retrain models
* automatically promote models
* replace the MLflow lifecycle
* override the baseline promotion guard

## Outcome

Monitoring information became accessible from the main application rather than requiring direct interaction with service endpoints.

---

# Phase 5 Batch 7 — Model Performance & Degradation Monitoring

## Status

**Complete**

## Objective

Track actual forecasting performance over time and detect sustained degradation.

## Prediction Records

The monitoring system records predictions independently from outcome observations.

A prediction can be recorded immediately:

```text
Prediction
   ↓
Prediction Record
```

A performance observation requires the corresponding actual value:

```text
Prediction
   +
Actual Outcome
   ↓
Performance Observation
```

This distinction prevents the system from pretending to know forecasting accuracy before the actual outcome exists.

## Performance Metrics

The performance monitoring layer calculates:

* MAE
* RMSE
* NMAE
* persistence MAE
* persistence RMSE
* persistence NMAE
* building-level metrics
* comparison with persistence

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

are required before the default sustained degradation decision can be evaluated.

The detector does not classify a model as degraded merely because one 30-observation window is poor.

The possible state is:

```text
insufficient_data
```

until sufficient observations exist.

## Degradation Threshold

The default relative degradation threshold is:

```text
10%
```

The detector evaluates degradation across sustained windows.

Conceptually:

```text
Recent Outcomes
      ↓
30-observation Window
      ↓
Performance Comparison
      ↓
Window Signal
      ↓
Repeat for 3 Windows
      ↓
Sustained Degradation Decision
```

## Baseline-Aware Performance

The persistence baseline is retained alongside model predictions.

This allows the monitoring system to compare:

```text
Served Model
     vs.
Persistence Baseline
```

using the same actual outcomes.

## Outcome

The project gained a performance-monitoring and sustained-degradation foundation suitable for the next lifecycle stage.

---

# Phase 5 Final Verification

## Status

**Complete**

## Automated Verification

The final Python test suite passed:

```text
47 passed
2 warnings
```

Ruff passed:

```text
All checks passed!
```

The API typecheck passed:

```text
tsc --noEmit
```

The API production build passed:

```text
tsc
```

The API lint check was included in the final CI verification.

The web lint check passed:

```text
eslint
```

The web production build passed:

```text
next build
```

The resulting application routes include:

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

## Runtime Verification

The containerized runtime was verified with:

```text
Web
API
Model Service
MLflow
```

The model-service runtime was rebuilt after the monitoring/inference instrumentation fixes so that the running container reflected the current application code.

The prediction path and Monitoring page were verified in the containerized application.

## Runtime Stability Fix

During Phase 5 integration verification, an optional weather field could be `None` in a valid prediction request.

Monitoring instrumentation originally attempted to convert the missing value directly to a float, causing:

```text
POST /predict
→ 500
```

The monitoring feature extraction was corrected so optional weather fields are included only when present.

The result is that observability instrumentation no longer breaks valid prediction requests.

## Testing of Sustained Degradation

An incorrect intermediate implementation allowed a single 30-observation window to produce a degraded decision.

The contract was corrected to require:

```text
90 outcome observations
=
3 × 30-observation windows
```

The integration tests were updated accordingly.

The final full Python suite passed after this correction.

---

# Phase 5 Engineering Decisions

## 1. Monitoring does not control production deployment

Monitoring produces evidence.

It does not directly promote or replace models.

## 2. Drift does not automatically trigger retraining

Feature drift is a signal.

Drift alone is insufficient evidence for retraining.

## 3. Performance requires actual outcomes

A prediction cannot be scored until its corresponding actual observation becomes available.

## 4. Sustained degradation is required

A single bad window should not trigger a lifecycle transition.

The current default requires three consecutive performance windows with sufficient observations.

## 5. Baseline comparison remains important

The persistence baseline remains part of performance monitoring so that model performance can be interpreted against a simple operational reference.

## 6. Insufficient data is a valid state

The monitoring system explicitly represents:

```text
insufficient_data
```

instead of manufacturing conclusions from too few observations.

## 7. Observability must not break inference

Monitoring instrumentation is secondary to the prediction contract.

Optional monitoring fields must therefore be handled safely.

## 8. Monitoring state is bounded

The local monitoring state is capped at 1000 observations.

This is appropriate for the current laptop-first architecture.

A persistent telemetry store can be introduced later if the deployment architecture requires it.

---

# Phase 5 Scope Boundary

Phase 5 intentionally does not implement:

* automatic retraining
* automatic model promotion
* automatic rollback
* cloud deployment
* Kubernetes
* production-scale telemetry infrastructure
* distributed monitoring
* large-scale streaming infrastructure

Phase 5 instead establishes the evidence layer required for controlled lifecycle decisions.

---

# Phase 5 Outcome

Phase 5 transformed the system from:

```text
A working ML application
```

into:

```text
A tested, CI-verified and observable ML application
```

The resulting lifecycle is:

```text
Data
  ↓
Feature Engineering
  ↓
Training
  ↓
Evaluation
  ↓
Model Registry
  ↓
Promotion Guard
  ↓
Serving
  ↓
Prediction Monitoring
  ↓
Data Quality
  ↓
Feature Drift
  ↓
Performance Monitoring
  ↓
Sustained Degradation Detection
```

The current serving state remains:

```text
Serving mode:
baseline

Strategy:
Persistence

Learned production alias:
none
```

The strongest evaluated learned candidate remains Random Forest under the current validation macro-building NMAE selection criterion, but it remains rejected because it did not pass the baseline guard.

Phase 5 does not change that lifecycle decision.

---

# Phase 6 — Controlled Retraining

## Status

**Planned**

## Objective

Introduce a controlled process for updating models when sufficient new data and evidence justify retraining.

Phase 6 builds directly on the monitoring and degradation state established in Phase 5.

## Retraining Eligibility

The intended eligibility contract is:

```text
Sufficient Observations
        +
Sustained Performance Degradation
        +
Supporting Drift Evidence Where Relevant
        +
Baseline Comparison
        +
Data Quality Not Critical
        +
Service State Acceptable
        ↓
Retraining Eligible
```

The eligibility state should contain enough information to explain the decision.

Relevant information includes:

* model identity
* serving mode
* performance state
* drift state
* data-quality state
* service state
* sample count
* monitoring window
* current metrics
* reference metrics
* baseline metrics
* degradation status
* reasons for eligibility

## Planned Workflow

```text
New Data
   ↓
Data Validation
   ↓
Data Quality Checks
   ↓
Feature Generation
   ↓
Training
   ↓
Evaluation
   ↓
Compare Against Current Serving Strategy
   ↓
Baseline Guard
   ↓
Candidate Registration
   ↓
Promotion Decision
```

Retraining must not automatically replace the existing serving strategy.

## Planned Controls

* reproducible training configuration
* dataset tracking
* experiment tracking
* candidate model registration
* evaluation gates
* baseline comparison
* promotion rules
* rollback capability
* retraining history
* explicit lifecycle decisions

## Retraining Trigger Principle

Potential signals include:

```text
New Data Available
        OR
Sustained Performance Degradation
        OR
Meaningful Data / Feature Distribution Change
```

These signals should feed an evidence-correlation process rather than directly bypassing evaluation.

## Phase 6 Outcome

The ML system will gain a controlled model-update lifecycle rather than relying on manual replacement of model artifacts.

---

# Phase 7 — Deployment & Production Delivery

## Status

**Planned**

## Objective

Make the containerized platform reproducibly deployable outside the local development environment.

## Planned Work

* deployment configuration
* environment-specific configuration
* production secrets/configuration handling
* container image management
* CI/CD pipeline
* automated quality gates
* deployment workflow
* deployment health checks
* rollback strategy
* cloud deployment

## CI/CD

The intended deployment pipeline is:

```text
Git Push
   ↓
Automated Tests
   ↓
Lint / Type Checks
   ↓
Application Builds
   ↓
Container Image Build
   ↓
Deployment Validation
   ↓
Deployment
```

Model-specific deployment remains subject to the evaluation and promotion policy established in Phase 4.

## Production Architecture

The target architecture is:

```text
                    ┌──────────────────┐
                    │    Web Client    │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │   Web Frontend   │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Application API  │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │   ML Service     │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │  Model Registry  │
                    └──────────────────┘
```

Monitoring and lifecycle infrastructure operate alongside the application services.

## Phase 7 Outcome

The system becomes reproducibly deployable with automated engineering quality gates and a defined production delivery process.

---

# Final Project Progression

The completed and planned project progression is:

```text
PHASE 0
Project Foundation
        ↓
PHASE 1
Data + Features + ML Baseline
        ↓
PHASE 2
ML Inference Service
        ↓
PHASE 3
Application Platform
        ↓
PHASE 4
MLOps + Model Lifecycle
        ↓
PHASE 5
Testing + CI + Observability
        ↓
PHASE 6
Controlled Retraining
        ↓
PHASE 7
Deployment + Production Delivery
```

The current project status is:

```text
Phase 0  ✓ Complete
Phase 1  ✓ Complete
Phase 2  ✓ Complete
Phase 3  ✓ Complete
Phase 4  ✓ Complete
Phase 5  ✓ Complete
Phase 6  → Planned
Phase 7  → Planned
```

---

# Completed System

At the end of Phase 5, the platform provides:

```text
                    ┌─────────────────────────┐
                    │       BDG2 Data         │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Validation + Features   │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Baselines + ML Models   │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Evaluation + MLflow     │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Model Registry           │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Promotion Guard          │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Controlled Serving       │
                    │ Learned / Baseline       │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ FastAPI Inference        │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Prediction Monitoring    │
                    └────────────┬────────────┘
                                 ↓
          ┌──────────────────────┼──────────────────────┐
          ↓                      ↓                      ↓
    Data Quality             Feature Drift        Performance
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Degradation Detection   │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Phase 6 Eligibility     │
                    │ Foundation               │
                    └─────────────────────────┘
```

---

# Engineering Principles Across All Phases

## 1. Build incrementally

Each phase adds one major engineering capability.

## 2. Preserve contracts

Later phases build on interfaces established by earlier phases.

## 3. Validate before advancing

Each phase should have explicit verification before becoming a dependency for the next phase.

## 4. Baselines before complexity

A complex learned model must demonstrate value against a simple reference.

## 5. Evaluation before deployment

A trained model is not automatically a production model.

## 6. Monitoring before retraining

The system should observe degradation before attempting to correct it.

## 7. Evidence before lifecycle action

Drift, performance, data quality, and service state should be interpreted together.

## 8. Keep failure states explicit

Examples include:

```text
rejected
insufficient_data
reference_unavailable
baseline serving
```

These are valid system states and should not be hidden.

## 9. Prefer reproducibility

Experiments, model versions, configurations, and lifecycle decisions should remain traceable.

## 10. Avoid unnecessary infrastructure complexity

The system is intentionally CPU-first and laptop-runnable.

Infrastructure should be introduced when it solves a concrete engineering problem.

---

# Current Architecture Maturity

The project has progressed through the following maturity levels:

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
        ↓
Phase 7
Production Deployment
```

The current completed architecture therefore demonstrates not only model training, but the surrounding engineering required to operate an ML forecasting system responsibly.

---

# Current End State Before Phase 6

At the end of Phase 5:

```text
ML Training                  ✓
Baseline Evaluation          ✓
Learned Model Evaluation     ✓
Feature Engineering          ✓
Inference Service            ✓
Application Integration     ✓
Docker                       ✓
MLflow                       ✓
Model Registry               ✓
Promotion Guard              ✓
Baseline Fallback            ✓
Model Lab                    ✓
Automated Tests              ✓
CI Verification              ✓
Prediction Monitoring        ✓
Data Quality Monitoring      ✓
Feature Drift Detection      ✓
Performance Monitoring       ✓
Building-Level Monitoring    ✓
Sustained Degradation        ✓
Monitoring Dashboard         ✓

Automatic Retraining         →
Controlled Promotion         ✓ Existing guard
Cloud Deployment             →
```

The next architectural step is therefore not another monitoring layer.

The next step is the controlled retraining lifecycle defined by Phase 6.

The central lifecycle remains:

```text
Build
  ↓
Validate
  ↓
Measure
  ↓
Register
  ↓
Promote Carefully
  ↓
Serve
  ↓
Monitor
  ↓
Detect Sustained Degradation
  ↓
Establish Retraining Eligibility
  ↓
Retrain Under Controlled Evaluation
```

Each phase should preserve the contracts and engineering decisions established by the previous phase rather than introducing unnecessary complexity prematurely.