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
Monitoring & Controlled Retraining
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
Production baseline:
Persistence

ML challenger:
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
* train/test evaluation
* baseline comparison
* model error analysis
* a versioned ML artifact
* the initial ML input/output contract

---

# Phase 2 — ML Inference Service

## Status

**Complete**

## Objective

Turn the Phase 1 Random Forest model into a standalone, validated inference service.

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
Random Forest Model
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
Random Forest inference
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
Phase 1 Random Forest Model
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
* application-level error handling

The API separates application concerns from ML inference concerns.

## Historical Consumption

The application reads the canonical Phase 1 feature dataset and exposes building-level historical consumption through the application API.

The frontend renders the resulting observations using a Recharts-based consumption chart.

## Forecast Integration

The application connects the frontend to the Phase 2 ML inference service.

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
Random Forest
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

## Validation

Phase 3 passed:

* Python test suite
* Node API type checking
* Node API production build
* Next.js linting
* Next.js production build
* end-to-end prediction verification

## Scope Boundary

Phase 3 intentionally does not introduce:

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

These capabilities are reserved for later phases.

## Phase 3 Outcome

The project now has a functional application platform:

```text
Web Application
      ↓
Application API
      ↓
ML Inference Service
      ↓
Machine Learning Model
```

---

# Phase 4 — MLOps & Model Lifecycle

## Status

**Next**

## Objective

Introduce reproducible experiment tracking and a controlled model lifecycle.

The goal is to move from:

```text
A trained model artifact
```

to:

```text
A managed model lifecycle
```

## Planned Work

### Experiment Tracking

Track:

* experiment configuration
* dataset version
* feature configuration
* model parameters
* evaluation metrics
* training timestamp
* model artifact references

### Model Registry

Introduce model versioning and lifecycle states.

The intended concept is:

```text
Experiment
    ↓
Candidate Model
    ↓
Evaluation
    ↓
Registered Model
    ↓
Champion / Challenger
```

### Evaluation Gates

A candidate model should not automatically become the production model.

Evaluation should compare it against the existing champion using predefined metrics and validation criteria.

The system should preserve the distinction between:

```text
Candidate
Champion
Challenger
```

### Model Promotion

Model promotion should be controlled and auditable.

A promotion workflow should record:

* model version
* evaluation metrics
* promotion decision
* timestamp
* previous champion
* new champion

## Phase 4 Outcome

The project should gain a reproducible and traceable model lifecycle.

---

# Phase 5 — Monitoring & Observability

## Status

**Planned**

## Objective

Monitor the behavior of the deployed ML system after inference.

Monitoring will cover both the software system and the ML system.

## Planned Monitoring Areas

### Data Quality

Monitor:

* missing values
* invalid values
* unexpected ranges
* schema changes
* timestamp continuity
* feature availability

### Data Drift

Monitor changes in feature distributions between historical/training data and incoming inference data.

Potential areas include:

* energy distributions
* weather variables
* calendar-related distributions
* building-level input distributions

### Prediction Performance

When actual future observations become available, compare:

```text
Predicted Energy
        vs.
Actual Energy
```

and track metrics over time.

### Service Health

Monitor:

* prediction latency
* request volume
* error rate
* service availability
* model loading status

## Planned Dashboard Information

The application can eventually expose operational ML information such as:

* active model version
* model status
* prediction latency
* prediction error rate
* data freshness
* drift status
* last successful inference
* retraining status

## Phase 5 Outcome

The project should become observable rather than simply operational.

---

# Phase 6 — Controlled Retraining

## Status

**Planned**

## Objective

Introduce a controlled process for updating models when new data becomes available or model performance deteriorates.

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
Compare Against Champion
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

## Phase 6 Outcome

The ML system gains a controlled model update lifecycle.

---

# Phase 7 — Containerization & Deployment

## Status

**Planned**

## Objective

Package the application and ML services into reproducible deployable units.

## Planned Work

* Dockerize frontend
* Dockerize application API
* Dockerize ML service
* establish service configuration
* establish environment-specific configuration
* compose local services
* introduce deployment configuration
* establish CI/CD pipeline
* deploy the application

## Target Architecture

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

## Phase 7 Outcome

The system becomes reproducibly deployable.

---

# Final Project Progression

The intended progression of the project is:

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
Containerization + Deployment
```

The key engineering principle is that each phase builds on the previous one without prematurely introducing infrastructure that is not yet required.

At the completion of Phase 3, the project has progressed from a data and ML pipeline into a functional end-to-end application.

The next major engineering step is therefore **Phase 4 — MLOps and Model Lifecycle Engineering**.