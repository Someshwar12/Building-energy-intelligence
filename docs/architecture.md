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

The system is developed incrementally so that each layer can be implemented, tested, validated, and documented before additional complexity is introduced.

The current implemented architecture is:

```text
                         Building & Energy Intelligence
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
   Data / ML                     Application                  ML Lifecycle
   Development                    Platform                    Management
        │                             │                             │
        ▼                             ▼                             ▼
   BDG2 Dataset                  Next.js / React               MLflow
        │                             │                             │
        ▼                             ▼                             ▼
   Feature Dataset               Express API              Model Registry
        │                             │                             │
        ▼                             ▼                             ▼
   ML Training                  FastAPI ML Service          Evaluation Gates
        │                             │                             │
        ▼                             ▼                             ▼
   Model Artifacts                 Inference              Promotion Guard
                                      │                             │
                                      └──────────────┬──────────────┘
                                                     ▼
                                             Serving Decision
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

The ML service is responsible for:

* request validation
* feature construction
* model loading
* inference
* prediction response

MLflow is responsible for:

* experiment tracking
* model artifact registration
* model versioning
* lifecycle metadata

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
ML Model
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
```

The initial evaluated models include:

* Persistence
* Ridge Regression
* Random Forest
* HistGradientBoosting

The persistence model is retained as the primary benchmark baseline.

Random Forest was retained as the initial learned ML challenger and deployable model artifact.

The local artifact is:

```text
models/random_forest_phase1.joblib
```

The project distinguishes between:

```text
Benchmark Baseline
Persistence

Learned ML Challenger
Random Forest
```

A learned model is not considered the production model simply because it is the strongest learned model.

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
└── model-lab/
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

Phase 4 introduced MLflow as the lifecycle management layer.

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
```

The system therefore separates:

```text
Model Development
        ↓
Model Management
        ↓
Model Serving
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
     ┌────┴────┐
     │         │
   PASS       FAIL
     │         │
     ▼         ▼
Production   Rejected
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

Its validation macro-building NMAE is:

```text
0.128728
```

The persistence baseline guard reference is:

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

Phase 4 introduced containerized local execution.

The complete local stack consists of four services:

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
   └──────────────► MLflow :5000
                         │
                         ▼
                   Model Registry
```

The application therefore has a complete request path from user interface to data access and ML inference.

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

## Database Boundary

A dedicated application database has not been introduced.

The current application does not require MongoDB or another application database because its present state can be represented through static application data, processed datasets, and MLflow lifecycle storage.

A database can be introduced later if requirements emerge for:

* user-specific state
* operational records
* prediction history
* configuration
* alerts
* monitoring records

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

# Testing Architecture

Each layer can be validated independently.

```text
Python Tests
      ↓
ML / Data Components

Node Type Checking + Build
      ↓
Application API

Next.js Lint + Build
      ↓
Frontend

Docker Runtime Checks
      ↓
Containerized System
```

The model-service test suite currently contains:

```text
20 passed
```

Phase 4 runtime verification also covered:

* Docker Compose configuration
* MLflow health
* model-service health
* model-service readiness
* API health
* registered model versions
* lifecycle metadata
* MLflow signatures
* real prediction execution
* baseline prediction behavior

---

# Current Service Responsibilities

| Component              | Responsibility                         |
| ---------------------- | -------------------------------------- |
| Next.js                | User interface and presentation        |
| React                  | UI components and client-side state    |
| Recharts               | Analytical visualization               |
| Express                | Application API and orchestration      |
| Building Repository    | Building metadata access               |
| Consumption Repository | Historical consumption access          |
| Prediction Repository  | Prediction-context preparation         |
| Building Service       | Building application logic             |
| Consumption Service    | Consumption application logic          |
| Prediction Service     | ML-service communication               |
| Anomaly Service        | Consumption anomaly analysis           |
| Model Lab Service      | ML lifecycle API integration           |
| FastAPI                | ML inference and serving strategy      |
| MLflow                 | Experiment tracking and model registry |
| Persistence            | Operational baseline forecasting       |
| Learned Models         | Evaluated forecasting challengers      |

---

# Phase 4 Architectural Outcome

Phase 4 extends the previous application architecture into a local MLOps system.

The resulting architecture is:

```text
                         ┌──────────────────────┐
                         │     Next.js Web      │
                         │        :3000         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Express API       │
                         │        :4000         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │  FastAPI ML Service  │
                         │        :8000         │
                         └──────────┬───────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
             Persistence Baseline          MLflow :5000
                                                   │
                                                   ▼
                                            Model Registry
                                                   │
                                                   ▼
                                            Model Versions
                                                   │
                                                   ▼
                                            Evaluation Gates
                                                   │
                                                   ▼
                                            Promotion Decision
```

The most important architectural result is the separation between:

```text
User Experience
       ↓
Application Logic
       ↓
ML Inference
       ↓
Model Lifecycle
       ↓
Model Artifact / Baseline
```

This separation allows the platform to evolve without coupling the frontend directly to model-training or model-management infrastructure.

---

# Completed Architecture

The completed current architecture is:

```text
                    ┌──────────────────────┐
                    │      BDG2 Data       │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ Validation + Feature │
                    │     Engineering      │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │ ML Training + Eval   │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │       MLflow         │
                    │ Experiment Tracking  │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │    Model Registry    │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │    Baseline Guard    │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │    Serving Decision  │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │   FastAPI Service    │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │    Express API       │
                    └──────────┬───────────┘
                               ↓
                    ┌──────────────────────┐
                    │    Next.js Web       │
                    └──────────────────────┘
```

---

# Future Architecture

Future phases will extend the current architecture with monitoring, controlled retraining, and deployment.

The intended evolution is:

```text
Experiment Tracking
        ↓
Model Registry
        ↓
Evaluation Gates
        ↓
Model Promotion
        ↓
Serving
        ↓
Monitoring
        ↓
Drift Detection
        ↓
Performance Detection
        ↓
Controlled Retraining
        ↓
Re-evaluation
        ↓
Promotion
        ↓
Deployment
```

These are future architectural capabilities, not requirements of the current completed phase.

---

# Phase 4 Scope Boundary

Phase 4 is complete.

It does not implement:

* GitHub Actions CI/CD
* production cloud deployment
* Kubernetes
* automated data-quality monitoring
* automated data-drift detection
* prediction-performance monitoring
* automated retraining
* automatic retraining triggers
* automatic production promotion without evaluation

These capabilities belong to later phases.

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
```

This provides a stable foundation for the next engineering stage without introducing monitoring, retraining, or deployment infrastructure prematurely.
