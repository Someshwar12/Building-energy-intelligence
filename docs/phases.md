# Project Phases

This project is developed as a staged machine-learning and software engineering system.

Each phase adds a distinct layer to the platform while preserving the interfaces and decisions established in previous phases.

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
Monitoring & Observability
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
* Ridge Regression
* Random Forest
* HistGradientBoosting

## Model Selection

The persistence model established the strongest baseline on the selected evaluation setup.

Random Forest was retained as the ML challenger and as the first deployable ML model for the subsequent inference-service phase.

The project therefore deliberately distinguishes:

```text
Production benchmark:
Persistence

Initial ML challenger:
Random Forest
```

The Random Forest model artifact is:

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
* versioned ML artifacts
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
ML Model
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

The inference service requires the historical context necessary to reproduce the Phase 1 feature construction.

The prediction workflow therefore uses:

```text
168 hours of historical observations
        +
building metadata
        +
weather context
        +
target timestamp
        ↓
Phase 1 feature construction
        ↓
ML inference
```

## Validation

Phase 2 established a tested ML service boundary.

The service was validated through:

* unit tests
* request validation tests
* model-loading tests
* inference tests
* real API prediction verification
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
ML Model
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

The consumption and forecast views are presented together because they form the primary analytical workflow.

## Additional Application Views

The application also provides dedicated analytical views for:

* Buildings
* Consumption
* Forecasts
* Anomalies
* Model Lab

These views expose the platform's application and ML capabilities without requiring users to interact directly with the underlying services.

## Validation

Phase 3 passed:

* Python test suite
* Node API type checking
* Node API production build
* Next.js linting
* Next.js production build
* end-to-end prediction verification

## Scope Boundary

Phase 3 intentionally did not introduce:

* MongoDB
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
┌─────────────────────────────┐
│ Does candidate beat baseline│
└──────────────┬──────────────┘
               │
        ┌──────┴──────┐
        │             │
       YES            NO
        │             │
        ▼             ▼
 @production       Reject Candidate
```

The promotion guard uses:

```text
validation_macro_building_nmae
```

as the learned-model evaluation metric.

The learned candidate is compared against the persistence baseline using the same metric definition.

This prevents a learned model from being promoted simply because it performs better than other learned models.

### Current Promotion Result

The current evaluated registry state does not contain a learned production model.

The persistence baseline remains the operational production strategy because no learned candidate passed the baseline guard.

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
* timezone
* weather variables
* calendar features
* cyclical time features
* historical energy lag features
* rolling energy statistics
* heating degree-hour features
* cooling degree-hour features

The model output is a numeric prediction tensor.

### Model Service Integration

The model service now obtains its model lifecycle information through MLflow when operating in MLflow mode.

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

The Docker Compose stack was successfully verified with all four services running.

Verified services:

```text
Web              : 3000
API              : 4000
Model Service    : 8000
MLflow           : 5000
```

Verified model-service endpoints:

```text
GET /health
GET /ready
POST /predict
```

The readiness state correctly exposes the active serving strategy.

A real prediction request successfully passed through the containerized inference path.

### Automated Verification

The complete model-service test suite passed:

```text
20 passed
```

The remaining HTTPX/Starlette messages were deprecation warnings and did not cause test failures.

## Model Lab

A Model Lab interface was added as an application-level observability surface for the MLflow lifecycle.

It exposes information such as:

* registered model versions
* model runs
* lifecycle metadata
* evaluation metadata
* baseline information
* production serving state
* model metrics
* model parameters
* registry state

The Model Lab interface is considered a supporting observability surface rather than a separate ML lifecycle phase.

Further UI/metadata refinement can be performed later if additional MLflow metadata needs to be surfaced.

## Phase 4 Outcome

Phase 4 established the project's first complete local MLOps lifecycle:

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

The following capabilities remain intentionally outside Phase 4:

* GitHub Actions CI/CD
* automated data-quality monitoring
* data drift detection
* prediction monitoring
* automated performance monitoring
* automated retraining
* retraining triggers
* cloud deployment
* Kubernetes
* large-scale distributed infrastructure
* large LLM or agent infrastructure

These capabilities belong to later phases only where they provide a concrete engineering benefit.

---

# Phase 5 — Monitoring & Observability

## Status

**Planned**

## Objective

Monitor the behavior of the application and ML system after inference.

Monitoring will cover both software-system health and ML-system behavior.

## Planned Monitoring Areas

### Data Quality

Monitor:

* missing values
* invalid values
* unexpected ranges
* schema changes
* timestamp continuity
* feature availability
* data freshness

### Data Drift

Monitor changes in feature distributions between historical/training data and incoming inference data.

Potential areas include:

* energy distributions
* weather variables
* calendar-related distributions
* building-level input distributions

### Prediction Monitoring

Track:

* prediction volume
* prediction distributions
* prediction latency
* prediction failures
* active model version
* serving mode

### Prediction Performance

When actual future observations become available, compare:

```text
Predicted Energy
        vs.
Actual Energy
```

and calculate relevant forecasting metrics over time.

### Service Health

Monitor:

* request latency
* request volume
* error rate
* service availability
* model loading status
* API health
* ML service readiness
* MLflow availability

## Planned Dashboard Information

The application can eventually expose operational ML information such as:

* active model version
* model status
* serving mode
* prediction latency
* prediction error rate
* data freshness
* drift status
* last successful inference
* monitoring status
* alert state

## Phase 5 Outcome

The project should become observable rather than simply operational.

The monitoring layer will provide the evidence required for later controlled retraining decisions.

---

# Phase 6 — Controlled Retraining

## Status

**Planned**

## Objective

Introduce a controlled process for updating models when new data becomes available or when model performance deteriorates.

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
Compare Against Current Champion / Baseline
   ↓
Promotion Decision
```

Retraining should not automatically replace the existing production model without evaluation.

## Planned Controls

* reproducible training configuration
* dataset tracking
* experiment tracking
* candidate model registration
* evaluation gates
* promotion rules
* rollback capability
* retraining history
* explicit lifecycle decisions

## Retraining Trigger Concept

A retraining workflow may eventually be triggered by conditions such as:

```text
New Data Available
        OR
Sustained Performance Degradation
        OR
Data / Feature Distribution Change
```

The trigger itself should not bypass evaluation.

The resulting model must pass the same lifecycle controls before becoming a production candidate.

## Phase 6 Outcome

The ML system gains a controlled model-update lifecycle rather than relying on manual replacement of model artifacts.

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

The deployment phase can introduce automated checks such as:

```text
Git Push
   ↓
Automated Tests
   ↓
Lint / Type Checks
   ↓
Build
   ↓
Container Image Build
   ↓
Deployment Validation
   ↓
Deployment
```

Model-specific deployment should remain subject to the evaluation and promotion policy established in Phase 4.

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

Monitoring and lifecycle infrastructure will operate alongside the application services.

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
Monitoring + Observability
        ↓
PHASE 6
Controlled Retraining
        ↓
PHASE 7
Deployment + Production Delivery
```

The current completed scope is:

```text
Phase 0  ✓
Phase 1  ✓
Phase 2  ✓
Phase 3  ✓
Phase 4  ✓
Phase 5  → Planned
Phase 6  → Planned
Phase 7  → Planned
```

The project has therefore progressed from a raw building-energy dataset to a containerized application with a validated ML inference service and a managed ML lifecycle.

The current system is intentionally local and CPU-first.

Future phases will add monitoring, controlled retraining, and deployment only when those capabilities solve concrete engineering requirements.

The key engineering principle remains:

```text
Build
  ↓
Validate
  ↓
Measure
  ↓
Document
  ↓
Commit
  ↓
Add the next layer
```

Each phase should preserve the contracts and engineering decisions established by the previous phase rather than introducing unnecessary complexity prematurely.
