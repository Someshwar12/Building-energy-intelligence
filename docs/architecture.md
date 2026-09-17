# Architecture

## Overview

The Building & Energy Intelligence Platform is designed as a layered machine-learning application.

The architecture separates:

- data processing
- machine-learning development
- ML inference
- application-level orchestration
- frontend presentation
- ML lifecycle management
- testing and continuous integration
- operational monitoring
- data-quality monitoring
- drift detection
- model-performance monitoring
- service health

The system is developed incrementally so that each layer can be implemented, tested, validated, and documented before additional complexity is introduced.

The current implemented architecture is:

```text
                         Building & Energy Intelligence
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
     Data / ML                   Application                ML Lifecycle
     Development                  Platform                   Management
          │                           │                           │
          ▼                           ▼                           ▼
      BDG2 Dataset              Next.js / React               MLflow
          │                           │                           │
          ▼                           ▼                           ▼
    Feature Dataset             Express API               Model Registry
          │                           │                           │
          ▼                           ▼                           ▼
     ML Training             FastAPI ML Service          Evaluation Gates
          │                           │                           │
          ▼                           │                           ▼
    Model Artifacts                   │                  Promotion Guard
          │                           │                           │
          └───────────────┐           │           ┌───────────────┘
                          ▼           ▼           ▼
                         Serving Decision
                                │
                                ▼
                         Monitoring Layer
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
                 Data       Drift       Performance
                Quality    Detection     Monitoring
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                         Service Health
                                │
                                ▼
                    Sustained Degradation
                                │
                                ▼
                     Phase 6 Eligibility
````

---

# Design Principles

The architecture follows several principles.

## Separation of Concerns

Each service has a clearly defined responsibility.

The frontend is responsible for:

* presentation
* user interaction
* analytical visualization
* frontend state

The application API is responsible for:

* application-level orchestration
* building metadata access
* historical consumption access
* prediction-context preparation
* communication with the ML service
* anomaly analysis
* application-level ML lifecycle access

The ML service is responsible for:

* request validation
* feature construction
* model loading
* inference
* prediction response
* monitoring instrumentation
* model lifecycle information
* performance and drift evaluation

MLflow is responsible for:

* experiment tracking
* model artifact registration
* model versioning
* lifecycle metadata

The monitoring layer is responsible for:

* prediction observations
* data-quality signals
* drift signals
* performance observations
* degradation analysis
* service-health signals

The ML model itself remains isolated from the application presentation layer.

---

## Explicit Service Boundaries

The frontend does not communicate directly with the FastAPI ML service.

Instead:

```text
Frontend
   ↓
Express API
   ↓
FastAPI ML Service
   ↓
ML Model / Serving Strategy
```

This creates a stable application boundary and allows the ML implementation to evolve independently from the user interface.

The ML lifecycle is also separated from the frontend:

```text
Training / Evaluation
        ↓
      MLflow
        ↓
  Model Registry
        ↓
 Promotion Decision
        ↓
FastAPI Serving
```

Monitoring is connected to the serving lifecycle but does not directly control model promotion or retraining:

```text
Prediction
    ↓
Monitoring
    ├── Data Quality
    ├── Drift
    ├── Performance
    └── Service Health
             ↓
      Degradation Evidence
             ↓
      Phase 6 Eligibility
```

---

## Reuse of Established ML Contracts

The application consumes the inference contract established during the ML-service phase.

The application does not independently recreate the ML model logic.

The FastAPI service remains responsible for:

* input validation
* historical-context validation
* feature construction
* model loading
* inference
* prediction response
* serving-mode identification
* monitoring instrumentation

This avoids duplicating ML logic across application layers.

---

## Feature Parity

The feature construction used during inference reproduces the feature definitions established during model development.

The current forecasting workflow requires:

```text
Historical observations
        +
Building metadata
        +
Weather context
        +
Target timestamp
        ↓
Feature Construction
        ↓
ML Inference
```

This preserves feature parity between training and inference and reduces the risk of training-serving skew.

The monitoring layer reuses the same relevant feature definitions when constructing monitoring observations.

---

## CPU-First Architecture

The initial platform is designed to run locally on a normal development laptop without requiring a GPU.

The current architecture therefore avoids:

* GPU-dependent infrastructure
* large transformer models
* LLM serving
* autonomous agents
* distributed training
* unnecessary cloud infrastructure

The architecture can evolve if a future requirement genuinely justifies additional infrastructure.

---

# System Layers

## Layer 1 — Data

The project begins with the Building Data Genome Project 2 (BDG2) dataset.

The main data flow is:

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

The canonical processed feature dataset is:

```text
data/processed/phase1_features.parquet
```

This dataset is used by the ML development pipeline and the current application-level historical consumption interface.

---

## Layer 2 — Machine Learning

The ML workflow is:

```text
Processed Dataset
      ↓
Train / Validation / Test
      ↓
Feature Construction
      ↓
Model Training
      ↓
Evaluation
      ↓
Model Artifact
      ↓
MLflow Tracking
      ↓
Model Registry
```

The evaluated models include:

* Persistence
* Ridge Regression
* Random Forest
* HistGradientBoosting

The persistence model is retained as the primary benchmark baseline.

The learned models are evaluated independently against the persistence baseline.

A learned model is not considered the production model simply because it is the strongest learned model.

The project therefore distinguishes between:

```text
Benchmark Baseline
Persistence

Learned ML Models
Ridge
Random Forest
HistGradientBoosting
```

Local model artifacts are stored under:

```text
models/
```

MLflow provides the versioned registry representation used by the lifecycle layer.

---

# Layer 3 — ML Inference Service

The ML model is exposed through a standalone FastAPI service.

Location:

```text
apps/model_service/
```

The service provides:

```text
POST /predict
GET  /health
GET  /ready
```

It also provides monitoring and Model Lab endpoints.

The inference flow is:

```text
Prediction Request
      ↓
Schema Validation
      ↓
Historical Context Validation
      ↓
Feature Construction
      ↓
Serving Strategy
      ↓
Learned Model OR Persistence Baseline
      ↓
Structured Prediction Response
      ↓
Monitoring Instrumentation
```

The service loads the required model configuration at startup and exposes an explicit readiness state.

---

# Prediction Contract

The current forecasting workflow requires:

```text
168 hourly historical observations
+
building metadata
+
weather context
+
target timestamp
```

The resulting feature vector is constructed using the same feature definitions established during model development.

This establishes the contract:

```text
Training Feature Definition
          ↓
        ML Model
          ↑
          │
Same Feature Definition
          ↑
Inference Feature Construction
```

---

# Layer 4 — Application API

The Node.js/Express application API provides the application-facing service boundary.

Location:

```text
apps/api/
```

Its responsibilities include:

* building discovery
* building metadata
* historical consumption retrieval
* prediction-context preparation
* communication with the FastAPI service
* anomaly analysis
* ML lifecycle information access
* application-level error handling

The internal structure follows:

```text
Routes
  ↓
Services
  ↓
Repositories
  ↓
Data / ML Service
```

This prevents route handlers from becoming responsible for data access and application logic simultaneously.

---

# Application API Routes

## Buildings

```text
GET /api/buildings
GET /api/buildings/:buildingId
```

These endpoints expose available buildings and their metadata.

---

## Consumption

```text
GET /api/buildings/:buildingId/consumption
```

This endpoint retrieves historical consumption for a selected building and requested time range.

The underlying historical data comes from:

```text
data/processed/phase1_features.parquet
```

---

## Forecast

```text
GET /api/buildings/:buildingId/forecast
```

This endpoint prepares the prediction context and sends the inference request to the FastAPI ML service.

The frontend therefore does not need to know how the prediction context is assembled.

---

## Anomalies

```text
GET /api/buildings/:buildingId/anomalies
```

The anomaly endpoint provides building-level anomaly analysis over historical consumption.

The current anomaly service uses a rolling statistical detection approach based on historical consumption behavior.

---

## Model Lab

```text
GET /api/model-lab/summary
GET /api/model-lab/versions
GET /api/model-lab/runs
```

These endpoints expose ML lifecycle information from the ML service to the application.

Model Lab is an observability surface over the MLflow lifecycle.

It does not perform training or independently decide which model becomes production.

---

## Monitoring

The application exposes monitoring information through the model-service monitoring endpoints and application integration.

The monitoring layer provides information about:

* prediction observations
* data quality
* drift
* model performance
* degradation state
* service health

Monitoring does not automatically retrain or replace models.

---

# Application Data Flow

## Building Discovery

```text
Next.js
   ↓
API Client
   ↓
Express /api/buildings
   ↓
Building Service
   ↓
Building Repository
   ↓
buildings.json
```

Building metadata used by the application is stored in:

```text
apps/api/src/data/buildings.json
```

---

## Historical Consumption

```text
Next.js Building Details
      ↓
API Client
      ↓
Express Consumption Route
      ↓
Consumption Service
      ↓
Consumption Repository
      ↓
phase1_features.parquet
      ↓
Consumption Response
      ↓
Consumption Chart
```

---

## Forecasting

```text
Next.js Building Details
      ↓
API Client
      ↓
Express Forecast Route
      ↓
Prediction Service
      ↓
Prediction Repository
      ↓
168-hour Historical Context
      ↓
FastAPI /predict
      ↓
Serving Strategy
      ↓
Learned Model / Persistence
      ↓
Prediction Response
      ↓
Express API
      ↓
Forecast UI
```

---

## Monitoring

```text
Prediction Request
      ↓
FastAPI
      ↓
Prediction
      ↓
Monitoring State
      ├── Prediction Record
      ├── Data Quality
      ├── Drift Signals
      ├── Service Health
      └── Model Identity
               ↓
       Actual Outcome Available
               ↓
       Performance Observation
               ↓
       Rolling Metrics
               ↓
       Degradation Evaluation
```

Monitoring observations are operational events and are separate from the historical training dataset.

A monitoring observation represents a recorded prediction event, not a building or a historical dataset row.

---

# Frontend Architecture

The frontend is located at:

```text
apps/web/
```

The application uses:

* Next.js
* React
* TypeScript
* Tailwind CSS
* Recharts

The current route structure includes:

```text
apps/web/src/app/

├── page.tsx
├── buildings/
│   ├── page.tsx
│   └── [buildingId]/
│       └── page.tsx
├── consumption/
│   └── page.tsx
├── forecasts/
│   └── page.tsx
├── anomalies/
│   └── page.tsx
├── model-lab/
│   └── page.tsx
└── monitoring/
    └── page.tsx
```

Shared application components are located under:

```text
apps/web/src/components/
```

The frontend API client is centralized in:

```text
apps/web/src/lib/api.ts
```

The client provides typed interfaces for application responses including:

* Building
* ConsumptionPoint
* Forecast
* Anomaly
* ModelVersion
* ModelLabSummary
* ModelLabRun
* Monitoring data

---

# Frontend Information Architecture

The application provides several complementary analytical views.

## Overview

The overview page provides a high-level view of the platform and access to building-level analysis.

```text
Overview
   ↓
Buildings
   ↓
Building Details
```

---

## Buildings

The buildings view provides access to the available building inventory and building-level metadata.

```text
Buildings
   ↓
Building
   ↓
Building Details
```

---

## Building Details

The building detail page provides the primary analytical workflow.

```text
Building Details
       │
       ├── Building Metadata
       │
       ├── Consumption
       │
       ├── Forecast
       │
       └── Building Profile
```

Consumption and forecast information are presented together because they represent related analytical information.

---

## Consumption

The consumption view provides historical energy analysis independent of the forecast workflow.

---

## Forecasts

The forecast view provides access to prediction-oriented analysis.

---

## Anomalies

The anomaly view surfaces statistically unusual consumption behavior.

---

## Model Lab

Model Lab provides visibility into:

* registered model versions
* evaluation state
* model runs
* baseline information
* lifecycle information
* serving state
* MLflow metrics and parameters

The interface is intentionally treated as an observability layer rather than as the ML lifecycle controller.

---

## Monitoring

The Monitoring page provides operational visibility into the prediction system.

It surfaces information such as:

* service status
* prediction observations
* serving model identity
* serving mode
* data-quality signals
* feature drift
* model performance
* persistence-baseline comparison
* degradation state
* recent monitoring information

The Monitoring page is intended to answer operational questions about the current prediction system without modifying its lifecycle state.

---

# Repository Layer

The Node application uses repositories to isolate data access from application logic.

Current repositories include:

```text
apps/api/src/repositories/

├── buildingRepository.ts
├── consumptionRepository.ts
└── predictionRepository.ts
```

### Building Repository

Responsible for retrieving building metadata.

### Consumption Repository

Responsible for reading historical consumption from the processed feature dataset.

### Prediction Repository

Responsible for preparing the historical and contextual information required by the ML inference service.

This separation allows data-access implementations to change without requiring route-level changes.

---

# Service Layer

Application logic is separated into services:

```text
apps/api/src/services/

├── buildingService.ts
├── consumptionService.ts
├── predictionService.ts
├── anomalyService.ts
└── modelLabService.ts
```

The services provide the application-level interface between routes, repositories, and external services.

The prediction service acts as the boundary between the Express application and FastAPI ML service.

The anomaly service encapsulates anomaly-detection logic.

The Model Lab service encapsulates communication between the application API and ML lifecycle endpoints.

---

# ML Lifecycle Architecture

MLflow provides the lifecycle management layer.

The lifecycle is:

```text
Data
  ↓
Feature Engineering
  ↓
Training
  ↓
Experiment Tracking
  ↓
Evaluation
  ↓
Model Registry
  ↓
Baseline Guard
  ↓
Lifecycle Decision
  ↓
Serving
  ↓
Monitoring
```

The system therefore separates:

```text
Model Development
        ↓
Model Management
        ↓
Model Serving
        ↓
Operational Monitoring
```

---

# MLflow Architecture

The local system uses MLflow for experiment tracking and model registry functionality.

The primary MLflow experiment is:

```text
building-energy-phase1
```

The registered model is:

```text
building-energy-forecast
```

Training records include information such as:

* model parameters
* validation metrics
* test metrics
* dataset/reference metadata
* configuration
* Git commit information
* model artifacts
* model signatures
* model-family information
* validation status

The registry provides versioned model artifacts rather than relying only on local `.joblib` files.

---

# Current Model Registry

The current registered learned models are:

```text
v1 — Ridge
v2 — Random Forest
v3 — HistGradientBoosting
```

Their registry state is governed by evaluation and lifecycle rules.

The current promotion state is:

```text
Learned Production Model
None

Operational Serving Strategy
Persistence Baseline
```

This is intentional.

The strongest learned candidate is not promoted when it fails the persistence-baseline guard.

---

# Evaluation-Driven Promotion

A learned model is not automatically promoted merely because it is the best learned model.

The promotion workflow is:

```text
Registered Learned Models
          ↓
Evaluated Learned Models
          ↓
Select Best Learned Model
          ↓
Validation Macro-Building NMAE
          ↓
Compare Against Persistence Baseline
          ↓
       Baseline Guard
          │
       ┌──┴──┐
       │     │
     PASS   FAIL
       │     │
       ▼     ▼
 Production Rejected
```

The learned-model promotion metric is:

```text
validation_macro_building_nmae
```

A learned model is eligible for production only when its evaluation result is better than the persistence baseline according to the promotion guard.

This prevents the system from promoting a learned model simply because it outperforms the other learned models.

---

# Current Promotion Result

The current promotion guard selected Random Forest v2 as the strongest evaluated learned candidate.

Its validation macro-building NMAE is approximately:

```text
0.128728
```

The persistence baseline guard reference is approximately:

```text
0.094865
```

The guard result is:

```text
BASELINE GUARD: FAILED
```

Therefore:

```text
Candidate Alias
Removed

Production Alias
Not Changed

Serving Strategy
Persistence Baseline
```

The system deliberately does not force a learned model into production.

---

# Baseline Serving

When no learned model owns the production alias, the model service can serve the persistence baseline.

The persistence strategy uses the most recent observed energy value as the next-hour prediction.

The runtime serving state is:

```text
serving_mode = baseline
model_name   = persistence
model_version = baseline
```

This is an intentional lifecycle state rather than a deployment error.

The resulting architecture is:

```text
Prediction Request
       ↓
FastAPI
       ↓
Model Loader / Serving Decision
       ↓
No Valid Learned Production Model
       ↓
Persistence Baseline
       ↓
Prediction Response
```

This allows the application to remain operational without bypassing the promotion guard.

---

# Model Signatures

The registered model versions were verified against the Docker-hosted MLflow server.

The model signatures contain the feature contract required by the forecasting pipeline, including:

* building identifiers
* site identifiers
* primary-use information
* building area information
* weather variables
* calendar features
* cyclical time features
* historical energy lag features
* rolling energy statistics
* heating degree-hour features
* cooling degree-hour features

Signature verification provides an additional check that registered model artifacts preserve the expected inference contract.

---

# Docker Architecture

The containerized local execution environment consists of four services:

```text
                          ┌─────────────────────┐
                          │   Next.js / React   │
                          │       :3000         │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │    Node / Express   │
                          │       :4000         │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │  FastAPI ML Service │
                          │       :8000         │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │       MLflow        │
                          │       :5000         │
                          └─────────────────────┘
```

Docker Compose provides the local service network and persistent MLflow storage.

The browser-facing API is:

```text
http://localhost:4000
```

The API communicates with the model service through the Compose network:

```text
http://model-service:8000
```

The model service communicates with MLflow through:

```text
http://mlflow:5000
```

---

# Container Responsibilities

## Web Container

```text
docker/web.Dockerfile
```

Responsible for the production Next.js application.

---

## API Container

```text
docker/api.Dockerfile
```

Responsible for the Node.js/Express application API.

The container includes the application data required by the API.

---

## Model Service Container

```text
docker/model-service.Dockerfile
```

Responsible for:

* FastAPI
* model loading
* feature construction
* inference
* MLflow model access
* baseline serving
* monitoring
* drift calculations
* performance calculations
* degradation detection

---

## MLflow Container

```text
docker/mlflow.Dockerfile
```

Responsible for:

* experiment tracking
* model registry
* lifecycle metadata
* persistent MLflow state

MLflow state is stored through a Docker volume.

---

# Runtime Architecture

The local runtime architecture is:

```text
Browser
   │
   ▼
Next.js :3000
   │
   ▼
Express API :4000
   │
   ├──────────────► Application Data
   │
   ▼
FastAPI :8000
   │
   ├──────────────► Persistence Baseline
   │
   ├──────────────► MLflow :5000
   │                         │
   │                         ▼
   │                    Model Registry
   │
   └──────────────► Monitoring
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Data Quality  Drift   Performance
              │          │          │
              └──────────┼──────────┘
                         ▼
                  Service Health
```

The application therefore has a complete request path from user interface to data access, ML inference, and operational monitoring.

---

# Monitoring Architecture

Phase 5 introduced an observability layer around the prediction service.

The monitoring architecture is:

```text
                    Prediction Request
                           │
                           ▼
                    Request Validation
                           │
                           ▼
                       Prediction
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
       Data Quality      Drift       Prediction
          Signals       Signals      Observation
             │             │             │
             │             │             ▼
             │             │       Actual Outcome
             │             │             │
             │             │             ▼
             │             │      Performance
             │             │       Observation
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    Monitoring State
                           │
                           ▼
                  Degradation Analysis
```

Monitoring is observational.

It does not directly retrain or promote models.

---

# Data-Quality Monitoring

The monitoring architecture considers common input-quality conditions including:

* required fields
* data types
* missing values
* invalid energy values
* duplicate timestamps
* timestamp ordering
* expected temporal frequency
* gaps
* building identity
* weather-field validity

Data-quality monitoring exists to distinguish model-performance problems from invalid or incomplete input data.

Critical data-quality problems should therefore be considered separately from genuine model degradation.

---

# Drift Monitoring

Phase 5 introduced reference-based feature drift detection using Population Stability Index (PSI).

The drift layer:

* loads a reference feature profile
* extracts monitoring features from prediction requests
* compares current observations against reference distributions
* calculates PSI
* assigns a monitoring status
* handles insufficient samples
* handles unavailable reference data
* ignores non-finite observations

The current thresholds are:

```text
Healthy:  PSI < 0.10
Warning:  0.10 <= PSI < 0.25
Critical: PSI >= 0.25
```

The minimum current sample count for feature drift evaluation is:

```text
30 observations
```

This prevents individual observations from being interpreted as statistically meaningful distribution drift.

Drift is a supporting signal and does not independently trigger retraining.

---

# Prediction Monitoring

Each prediction can be associated with:

* building ID
* prediction timestamp
* predicted energy
* persistence baseline
* model name
* model version
* serving mode

The monitoring layer therefore preserves the identity of the prediction that was actually served.

A monitoring observation represents an operational prediction event.

It does not represent:

* one building
* one historical dataset row
* one training sample

This distinction keeps operational monitoring separate from the historical training dataset.

---

# Model Performance Monitoring

Phase 5 added outcome-based performance tracking.

A prediction becomes a performance observation when the corresponding actual energy value is available.

For each outcome, the system records:

* prediction
* actual value
* persistence baseline
* absolute error
* squared error
* building ID
* timestamp
* model identity
* serving mode

The system calculates:

* MAE
* RMSE
* NMAE
* persistence-baseline MAE
* persistence-baseline RMSE
* persistence-baseline NMAE

Performance can also be calculated per building.

This allows both global and building-level performance analysis.

---

# Baseline-Aware Performance

The persistence baseline is retained as a reference throughout monitoring.

The persistence strategy is:

```text
Use the latest observed energy value
as the next-hour prediction.
```

Performance monitoring therefore compares:

```text
Served model
      vs
Persistence baseline
```

on the same observed outcomes.

This prevents model-performance monitoring from evaluating a learned model without a simple operational reference.

---

# Sustained Degradation Detection

Phase 5 added explicit sustained-degradation logic.

The system does not classify a model as degraded because of one poor prediction or one poor rolling window.

The configured defaults are:

```text
Recent window size:          30 observations
Sustained windows required:  3
Relative degradation limit: 10%
Minimum observations:       90
```

The evaluation therefore requires:

```text
30 observations
    ↓
First performance window

30 observations
    ↓
Second performance window

30 observations
    ↓
Third performance window

90 observations total
    ↓
Sustained-degradation evaluation
```

The degradation detector requires all three evaluated windows to satisfy the degradation condition before returning a degraded state.

With fewer than 90 performance observations, the system returns:

```text
insufficient_data
```

This deliberately reduces the chance of triggering lifecycle actions from short-lived noise.

---

# Degradation State Semantics

The degradation evaluation distinguishes between:

```text
insufficient_data
healthy
degraded
```

### insufficient_data

There are not enough outcome observations to establish the required sustained performance window.

### healthy

There is sufficient data, but the sustained degradation condition has not been met.

### degraded

There is sufficient data and all required sustained windows satisfy the degradation condition.

This state is an evidence signal and does not itself retrain or replace a model.

---

# Service Health

The monitoring architecture considers:

* request availability
* prediction errors
* request latency
* health state
* readiness state
* dependency/service availability

The model service exposes health and readiness endpoints independently from the prediction endpoint.

This separates:

```text
Service is running
```

from:

```text
Service is ready to serve predictions
```

and from:

```text
Model performance is healthy
```

These are different operational conditions and are monitored separately.

---

# Monitoring State

The monitoring state is maintained by the model service.

The monitoring state stores:

* prediction records
* performance observations
* service-health information
* monitoring summaries

The in-memory monitoring store is bounded to prevent unbounded growth.

The monitoring layer is intentionally lightweight and suitable for the current local, CPU-first architecture.

A persistent production telemetry store can be introduced in a future phase if operational requirements justify it.

---

# Monitoring Dashboard

The Monitoring page exposes the operational state of the ML system through the web application.

The dashboard integrates the monitoring information required for Phase 5, including:

* service state
* prediction observations
* model/serving information
* data-quality signals
* drift signals
* performance information where outcomes exist
* baseline comparison
* degradation state
* recent monitoring information

The dashboard is an operational observability surface rather than a training notebook replacement.

---

# Testing Architecture

Phase 5 established automated verification across the major system layers.

The testing architecture is:

```text
Python Tests
      ↓
ML / Data / Monitoring Components

Node Type Checking + Build
      ↓
Application API

Next.js Lint + Build
      ↓
Frontend

Docker Runtime Verification
      ↓
Containerized System
```

The Python test suite covers:

* data validation
* feature generation
* lag correctness
* rolling-window behavior
* missing-history handling
* model behavior
* prediction contracts
* baseline behavior
* inference API
* monitoring
* drift
* performance
* degradation detection

Final Python test result:

```text
47 passed, 2 warnings
```

The API was verified with:

```text
npm run typecheck
npm run build
```

Both passed.

The API currently does not define an `npm run lint` script, so API linting is not part of the implemented project verification contract.

The frontend was verified with:

```text
npm run lint
npm run build
```

Both passed.

---

# Continuous Integration

GitHub Actions provides automated repository-level verification.

The CI foundation focuses on deterministic checks that are appropriate for regular changes.

The current verification categories are:

```text
Python
├── pytest
└── Ruff

Node API
├── TypeScript typecheck
└── production build

Web
├── ESLint
└── production build
```

The CI system intentionally avoids requiring expensive operations for every change.

The following are not required on every commit:

* complete historical retraining
* large-scale model evaluation
* long-running drift analysis
* full Docker stack rebuild
* large data ingestion
* production-style deployment

These can be introduced into scheduled or manual workflows when appropriate.

---

# CI Failure Boundaries

The following failures are intended to block a change:

* failing Python tests
* Ruff violations
* API type errors
* API build failures
* frontend lint failures
* frontend build failures

The purpose of CI is to catch deterministic engineering regressions before they reach the shared repository.

---

# Error Handling

The architecture separates internal errors from user-facing API responses.

For example:

```text
ML Service Failure
      ↓
Prediction Service
      ↓
Express Error Boundary
      ↓
Structured API Error
      ↓
Frontend Error State
```

This prevents internal implementation details from being exposed directly to the user interface.

The frontend provides explicit states for:

* loading
* unavailable data
* empty data
* unavailable forecasts
* unavailable buildings
* unavailable anomaly analysis
* unavailable Model Lab information
* unavailable monitoring information

---

# Prediction Reliability Boundary

Monitoring must not become a failure point for the prediction path.

The intended request path is:

```text
Request
  ↓
Validation
  ↓
Prediction
  ↓
Monitoring Instrumentation
```

Optional monitoring fields are handled safely so that missing optional information does not cause an otherwise valid prediction request to fail.

This preserves the primary application capability:

```text
building data → forecast
```

while still allowing operational telemetry to be collected.

---

# Data Storage Strategy

The current architecture deliberately keeps storage simple.

## Raw Data

```text
data/raw/
```

Contains source dataset material used during development.

---

## Processed Data

```text
data/processed/
```

Contains the canonical Phase 1 feature dataset.

---

## Model Artifacts

```text
models/
```

Contains local trained model artifacts.

MLflow additionally stores registered model versions and artifacts for lifecycle management.

---

## Application Metadata

```text
apps/api/src/data/
```

Contains building metadata consumed by the application API.

---

## MLflow Storage

MLflow uses persistent Docker storage for:

* experiment metadata
* registry metadata
* model lifecycle state
* tracked artifacts

---

## Monitoring Storage

The current monitoring implementation maintains operational observations in bounded in-memory state inside the model service.

This is sufficient for the current local architecture.

A persistent monitoring datastore can be introduced in a later phase if the system requires durable historical telemetry, multi-instance monitoring, or long-term alert history.

---

## Database Boundary

A dedicated application database has not been introduced.

The current application does not require MongoDB or another application database because its present state can be represented through static application data, processed datasets, MLflow lifecycle storage, and bounded monitoring state.

A database can be introduced later if requirements emerge for:

* user-specific state
* operational records
* persistent prediction history
* configuration
* alerts
* durable monitoring records

---

# Architecture Boundaries

The following boundaries are intentionally maintained.

## Frontend → Application API

The frontend communicates through the typed application API client.

```text
Next.js
   ↓
apps/web/src/lib/api.ts
   ↓
Express API
```

The frontend does not directly access application data files or ML model artifacts.

---

## Application API → ML Service

The Express API communicates with FastAPI for predictions.

```text
Express
   ↓
Prediction Service
   ↓
FastAPI /predict
```

The Express layer does not implement the forecasting model.

---

## ML Service → Model Lifecycle

The ML service is responsible for serving the currently valid model strategy.

```text
FastAPI
   ↓
Model Loader
   ↓
MLflow Model Registry
   ↓
Production Model
```

If no valid learned production model is available:

```text
FastAPI
   ↓
Serving Decision
   ↓
Persistence Baseline
```

---

## Training → Registry

Training and evaluation are separate from serving.

```text
Training
   ↓
Evaluation
   ↓
MLflow
   ↓
Model Registry
```

The serving service does not retrain models.

---

## Promotion → Production

Promotion is controlled by an explicit evaluation gate.

```text
Evaluated Candidate
        ↓
Baseline Guard
        ↓
Production Alias
```

A failed guard does not overwrite the existing production state.

---

## Serving → Monitoring

The prediction service emits operational information into the monitoring layer.

```text
Serving
   ↓
Prediction Record
   ├── Data Quality
   ├── Drift
   ├── Performance
   └── Service Health
```

Monitoring does not directly alter serving state.

---

# Phase 5 Monitoring Boundary

Phase 5 establishes a strict boundary between observation and automated lifecycle action.

```text
Prediction
    ↓
Observation
    ↓
Metrics
    ↓
Signals
    ↓
Sustained Evidence
    ↓
Retraining Eligibility
    ↓
PHASE 6
```

The current system stops before automatic retraining.

This prevents noisy monitoring signals from causing uncontrolled model lifecycle actions.

---

# Phase 6 Retraining Eligibility

Phase 5 establishes the evidence required before future retraining logic can be introduced.

A future retraining workflow should require sufficient evidence across multiple signals.

The intended conditions are:

```text
Sufficient observations
        +
Sustained performance degradation
        +
Supporting drift evidence where relevant
        +
Learned model underperforms persistence baseline
        +
Data quality is not critical
        +
Service state is operational
        ↓
Retraining Eligible
```

Drift alone must not trigger retraining.

Poor performance caused by critical data-quality problems must not automatically trigger retraining.

Short-lived degradation must not trigger retraining.

The resulting eligibility state should contain enough context to explain why retraining became eligible.

Expected future eligibility information includes:

* model identity
* model version
* serving mode
* sample count
* evaluation window
* current performance
* reference performance
* persistence-baseline performance
* drift state
* data-quality state
* service-health state
* degradation state
* reasons for eligibility

The actual retraining workflow is deferred to Phase 6.

---

# Current Service Responsibilities

| Component              | Responsibility                              |
| ---------------------- | ------------------------------------------- |
| Next.js                | User interface and presentation             |
| React                  | UI components and client-side state         |
| Recharts               | Analytical visualization                    |
| Express                | Application API and orchestration           |
| Building Repository    | Building metadata access                    |
| Consumption Repository | Historical consumption access               |
| Prediction Repository  | Prediction-context preparation              |
| Building Service       | Building application logic                  |
| Consumption Service    | Consumption application logic               |
| Prediction Service     | ML-service communication                    |
| Anomaly Service        | Consumption anomaly analysis                |
| Model Lab Service      | ML lifecycle API integration                |
| FastAPI                | ML inference and serving strategy           |
| MLflow                 | Experiment tracking and model registry      |
| Monitoring State       | Prediction and operational observations     |
| Drift Layer            | Reference-based feature drift detection     |
| Performance Layer      | Outcome-based model performance analysis    |
| Degradation Layer      | Sustained performance degradation detection |
| Persistence            | Operational baseline forecasting            |
| Learned Models         | Evaluated forecasting challengers           |

---

# Current Architecture Flow

The complete implemented architecture is:

```text
                         ┌──────────────────────┐
                         │      BDG2 Data       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Validation + Feature │
                         │     Engineering      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ ML Training + Eval   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       MLflow         │
                         │ Experiment Tracking  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Model Registry    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Baseline Guard    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Serving Decision  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   FastAPI Service    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Prediction       │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
          Data Quality           Drift            Performance
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    │
                                    ▼
                            Service Health
                                    │
                                    ▼
                         Sustained Degradation
                                    │
                                    ▼
                         Retraining Eligibility
                                    │
                                    ▼
                              Phase 6
                                   
                                   
                         ┌──────────────────────┐
                         │    Express API       │
                         │        :4000         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Next.js Web       │
                         │        :3000         │
                         └──────────────────────┘
```

---

# Completed Architecture

The current platform combines the application, ML lifecycle, and observability layers:

```text
                     ┌──────────────────────────┐
                     │        BDG2 Data         │
                     └────────────┬─────────────┘
                                  ↓
                     ┌──────────────────────────┐
                     │ Validation + Features    │
                     └────────────┬─────────────┘
                                  ↓
                     ┌──────────────────────────┐
                     │ Training + Evaluation     │
                     └────────────┬─────────────┘
                                  ↓
                     ┌──────────────────────────┐
                     │         MLflow            │
                     └────────────┬─────────────┘
                                  ↓
                     ┌──────────────────────────┐
                     │     Model Registry       │
                     └────────────┬─────────────┘
                                  ↓
                     ┌──────────────────────────┐
                     │      Baseline Guard      │
                     └────────────┬─────────────┘
                                  ↓
                     ┌──────────────────────────┐
                     │    Serving Decision       │
                     └────────────┬─────────────┘
                                  ↓
                     ┌──────────────────────────┐
                     │    FastAPI ML Service     │
                     └────────────┬─────────────┘
                                  ↓
                     ┌──────────────────────────┐
                     │       Prediction          │
                     └────────────┬─────────────┘
                                  ↓
               ┌──────────────────┼──────────────────┐
               ↓                  ↓                  ↓
          Data Quality          Drift          Performance
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  ↓
                           Service Health
                                  ↓
                      Sustained Degradation
                                  ↓
                       Phase 6 Eligibility
```

The application path remains:

```text
User Experience
       ↓
Application Logic
       ↓
ML Inference
       ↓
Model Lifecycle
       ↓
Monitoring
       ↓
Evidence for Future Lifecycle Actions
```

This separation allows the platform to evolve without coupling the frontend directly to model-training, model-management, or monitoring infrastructure.

---

# Phase 5 Architectural Outcome

Phase 5 extends the previous MLOps architecture with testability and operational observability.

The resulting architecture is:

```text
Training
   ↓
Tracking
   ↓
Evaluation
   ↓
Registry
   ↓
Baseline Guard
   ↓
Controlled Serving
   ↓
Prediction Monitoring
   ├── Data Quality
   ├── Drift
   ├── Performance
   └── Service Health
            ↓
     Sustained Evidence
            ↓
     Retraining Eligibility
            ↓
          Phase 6
```

The most important architectural result is that the platform can now observe the operational behavior of the prediction system without automatically modifying the model lifecycle.

---

# Phase 5 Scope Boundary

Phase 5 is complete.

It implements:

* automated testing
* Python static analysis
* API type checking
* API production verification
* frontend linting
* frontend production verification
* CI foundation
* data-quality monitoring
* feature drift detection
* prediction monitoring
* model-performance monitoring
* baseline-aware performance comparison
* sustained degradation detection
* service-health monitoring
* monitoring dashboard
* Phase 6 retraining eligibility contract

It does not implement:

* automatic retraining
* automatic model replacement
* automatic model promotion based solely on monitoring
* autonomous remediation
* production cloud deployment
* Kubernetes
* uncontrolled lifecycle actions

The current architecture deliberately stops at:

```text
Training
  ↓
Tracking
  ↓
Evaluation
  ↓
Registry
  ↓
Baseline Guard
  ↓
Controlled Serving
  ↓
Monitoring
  ↓
Sustained Evidence
  ↓
Retraining Eligibility