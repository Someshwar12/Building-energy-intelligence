# Architecture

## Overview

The Building & Energy Intelligence Platform is designed as a layered machine-learning application.

The architecture separates:

- data processing
- machine-learning development
- ML inference
- application-level orchestration
- frontend presentation

The system is being developed incrementally so that each layer can be tested independently before additional infrastructure is introduced.

The current implemented architecture is:

```text
┌──────────────────────────────────────────────┐
│              Next.js / React                 │
│                                              │
│  Overview                                    │
│  Building Details                            │
│  Consumption Visualization                   │
│  Forecast Display                            │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│            Node.js / Express                 │
│                                              │
│  Building API                                │
│  Consumption API                             │
│  Prediction Context                          │
│  Application-level orchestration             │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│             FastAPI ML Service               │
│                                              │
│  Request Validation                           │
│  Feature Construction                         │
│  Model Loading                                │
│  Inference                                    │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          Phase 1 Random Forest Model         │
└──────────────────────────────────────────────┘
````

---

## Design Principles

The architecture follows several principles.

### Separation of concerns

Each service has a clearly defined responsibility.

The frontend is responsible for presentation and user interaction.

The application API is responsible for application-level orchestration and data access.

The ML service is responsible for machine-learning inference.

The ML model itself remains isolated from the application presentation layer.

---

### Explicit service boundaries

The frontend does not communicate directly with the FastAPI ML service.

Instead:

```text
Frontend → Express API → FastAPI ML Service
```

This creates a stable application boundary and allows the ML implementation to evolve independently from the user interface.

---

### Reuse of established ML contracts

The Phase 3 application consumes the inference contract established during Phase 2.

The application does not independently recreate the ML model logic.

The FastAPI service remains responsible for:

* input validation
* feature construction
* model loading
* inference
* prediction response

This avoids duplicating ML logic across application layers.

---

### Incremental architecture

The system is intentionally built in phases.

The current architecture should not be interpreted as the final production architecture.

Infrastructure such as experiment tracking, model registries, monitoring, retraining, containerization, and deployment will be introduced only when their corresponding phases are reached.

---

# System Layers

## Layer 1 — Data

The project begins with the BDG2 dataset.

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

This dataset is shared by the ML development pipeline and the current application-level historical consumption interface.

---

## Layer 2 — Machine Learning

Phase 1 established the initial forecasting pipeline.

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
```

The initial ML models included:

* Persistence
* Ridge Regression
* Random Forest
* HistGradientBoosting

The persistence model remains the strongest benchmark baseline.

The Random Forest model was retained as the first ML challenger and deployable model artifact.

The artifact is:

```text
models/random_forest_phase1.joblib
```

---

## Layer 3 — ML Inference Service

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
Random Forest Inference
      ↓
Structured Prediction Response
```

The service loads the model artifact at startup and verifies that the artifact contains the expected structure.

---

# Prediction Contract

The prediction service expects the historical context required to reproduce the Phase 1 feature construction.

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

The resulting feature vector is constructed using the same feature definitions used during Phase 1.

This provides feature parity between training and inference.

---

# Layer 4 — Application API

The Node.js/Express application API was introduced in Phase 3.

Location:

```text
apps/api/
```

Its purpose is to provide an application-facing API rather than exposing the ML service directly to the frontend.

The application API is responsible for:

* building discovery
* building metadata
* historical consumption retrieval
* prediction-context preparation
* communication with the FastAPI service
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

---

## Application API Routes

### Buildings

```text
GET /api/buildings
GET /api/buildings/:buildingId
```

These endpoints expose the available buildings and their metadata.

---

### Consumption

```text
GET /api/buildings/:buildingId/consumption
```

This endpoint retrieves historical consumption for a selected building and requested time range.

The underlying historical data comes from:

```text
data/processed/phase1_features.parquet
```

---

### Forecast

```text
GET /api/buildings/:buildingId/forecast
```

This endpoint prepares the prediction context and sends the inference request to the FastAPI ML service.

The frontend therefore does not need to know how the prediction context is assembled.

---

# Application Data Flow

## Building Discovery

```text
Next.js Overview
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
168-hour historical context
      ↓
FastAPI /predict
      ↓
Random Forest Model
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

The current structure is:

```text
apps/web/src/
├── app/
│   ├── buildings/
│   │   └── [buildingId]/
│   │       └── page.tsx
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   └── ConsumptionChart.tsx
└── lib/
    └── api.ts
```

The frontend API client is centralized in:

```text
apps/web/src/lib/api.ts
```

The client provides typed interfaces for application responses such as:

* Building
* ConsumptionPoint
* Forecast

---

# Frontend Information Architecture

The application currently provides two primary views.

## Overview

The overview page provides access to the available buildings.

```text
Overview
   ↓
Building List
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
      ├── Consumption ───────── Forecast
      │
      └── Building Profile
```

The consumption and forecast views are placed together because they represent related analytical information.

The building profile is presented separately as contextual metadata.

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

Responsible for reading historical consumption from the processed Parquet dataset.

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
└── predictionService.ts
```

The services provide the application-level interface between routes and repositories/external services.

The prediction service additionally acts as the boundary between the Express application and FastAPI ML service.

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

The frontend also provides explicit states for:

* loading
* unavailable data
* empty data
* unavailable forecasts
* unavailable buildings

---

# Current Service Responsibilities

| Component              | Responsibility                      |
| ---------------------- | ----------------------------------- |
| Next.js                | User interface and presentation     |
| React                  | UI components and client-side state |
| Recharts               | Consumption visualization           |
| Express                | Application API and orchestration   |
| Building Repository    | Building metadata access            |
| Consumption Repository | Historical consumption access       |
| Prediction Repository  | Prediction context preparation      |
| Prediction Service     | ML-service communication            |
| FastAPI                | ML inference                        |
| Random Forest          | Energy prediction                   |

---

# Current Runtime Architecture

During local development, the system consists of three application services:

```text
┌─────────────────────┐
│   Next.js :3000     │
│      Frontend       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Express :4000     │
│   Application API   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   FastAPI :8000     │
│    ML Inference     │
└─────────────────────┘
```

The local application therefore provides a complete request path from user interface to model inference.

---

# Data Storage Strategy

The current phase deliberately keeps storage simple.

### Raw data

```text
data/raw/
```

Contains the source dataset used during development.

### Processed data

```text
data/processed/
```

Contains the canonical Phase 1 feature dataset.

### Model artifacts

```text
models/
```

Contains trained model artifacts.

### Application metadata

```text
apps/api/src/data/
```

Contains the building metadata consumed by the application API.

A dedicated application database has not yet been introduced.

---

# Architecture Boundaries

The following boundaries are intentionally maintained.

## Frontend ↔ Application API

The frontend communicates through the typed application API client.

```text
Next.js
   ↓
apps/web/src/lib/api.ts
   ↓
Express API
```

---

## Application API ↔ ML Service

The Express API communicates with FastAPI for predictions.

```text
Express
   ↓
Prediction Service
   ↓
FastAPI /predict
```

The Express layer does not implement the Random Forest model.

---

## ML Service ↔ Model Artifact

The FastAPI service owns model loading and inference.

```text
FastAPI
   ↓
Model Loader
   ↓
random_forest_phase1.joblib
```

This prevents application-layer code from depending directly on the serialized model.

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
```

The Phase 3 implementation was validated with:

```text
pytest -p no:cacheprovider
npm run typecheck
npm run build
npm run lint
```

All relevant validation checks passed.

---

# Architecture Evolution

The architecture is intentionally designed to evolve.

The current system:

```text
Data
  ↓
ML Model
  ↓
FastAPI
  ↓
Express
  ↓
Next.js
```

is the foundation for the future MLOps architecture.

The planned evolution is:

```text
                    ┌──────────────────────┐
                    │     Next.js Web      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Express API        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI ML Service │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Model Registry     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Champion / Candidate │
                    │       Models         │
                    └──────────────────────┘
```

Later phases will extend this with:

```text
Experiment Tracking
        ↓
Model Registry
        ↓
Evaluation Gates
        ↓
Model Promotion
        ↓
Monitoring
        ↓
Drift Detection
        ↓
Controlled Retraining
        ↓
Deployment
```

These components are planned architecture rather than current implemented functionality.

---

# Phase 3 Architectural Outcome

Phase 3 establishes the application layer without coupling it to future infrastructure.

The completed architecture now provides:

```text
Data
 ↓
Feature Dataset
 ↓
ML Model
 ↓
ML Inference Service
 ↓
Application API
 ↓
Web Application
```

The most important architectural result is the separation between:

```text
User Experience
        ↓
Application Logic
        ↓
ML Inference
        ↓
Model
```

This separation provides a stable foundation for the next phase of the project.

---

# Next Architectural Stage

The next phase will introduce **MLOps and model lifecycle engineering**.

The focus will shift from serving a trained model to managing models throughout their lifecycle:

```text
Experiment
   ↓
Training
   ↓
Evaluation
   ↓
Registration
   ↓
Champion / Challenger
   ↓
Promotion
   ↓
Monitoring
   ↓
Retraining
```

The current Phase 3 architecture is designed to accommodate these capabilities without requiring the frontend or application API to directly manage the machine-learning lifecycle.
## Phase 4 � Reproducibility, MLflow & Model Lifecycle

Phase 4 introduced reproducible local infrastructure and ML lifecycle management around the existing forecasting system.

### Containerized architecture

The application now runs locally through Docker Compose as four services:

- Web � React / Next.js
- API � Node / Express
- Model Service � FastAPI
- MLflow � experiment tracking and model registry

The browser-facing API uses `http://localhost:4000`, while the API communicates with the model service through the Compose network at `http://model-service:8000`.

The model service communicates with MLflow through `http://mlflow:5000`.

### MLflow experiment tracking

Training records:

- model parameters
- validation and test metrics
- dataset/reference metadata
- configuration
- Git commit information
- model artifacts
- model signatures

The experiment is stored under the `building-energy-phase1` MLflow experiment.

### Model Registry

The registered model is:

`building-energy-forecast`

Current registered versions:

- v1 � Ridge
- v2 � Random Forest
- v3 � HistGradientBoosting

The registry therefore provides versioned model artifacts rather than relying only on local `.joblib` files.

### Promotion policy

A learned model is not automatically promoted merely because it is the best learned model.

The promotion process first identifies the best evaluated learned model using validation macro-building NMAE and compares it against the persistence baseline using the same metric.

A learned model is assigned the production alias only if it beats the persistence baseline.

This prevents a weaker learned model from being presented as production-ready.

### Current serving state

The persistence baseline currently remains the serving model because the evaluated learned models did not beat it on validation macro-building NMAE.

The model service therefore supports:

`serving_mode = baseline`

with:

`model_name = persistence`

and:

`model_version = baseline`

This is an intentional lifecycle state, not a deployment error.

### Baseline fallback

When no valid MLflow `@production` alias exists, the model service can serve the persistence baseline.

The baseline prediction uses the most recent observed energy value from the supplied history.

This allows the application to remain operational without bypassing the model-promotion guard.

### Model signatures

The registered v1, v2 and v3 models were verified against the Docker-hosted MLflow server.

Each model exposes a compatible MLflow signature containing the building metadata, weather features, calendar features, lag features, rolling features and degree-hour features required by the forecasting pipeline.

### Verification

Phase 4 verification completed successfully:

- Docker Compose configuration validated.
- MLflow container healthy.
- Model service `/health` returned 200 OK.
- Model service `/ready` returned `ready`.
- API `/health` returned `ok`.
- All 20 automated tests passed.
- Registered model versions and lifecycle tags inspected.
- MLflow signatures verified for v1, v2 and v3.
- Real prediction request successfully passed through the running model service.
- Baseline prediction returned the latest supplied history value.

### Scope boundary

Phase 4 does not implement:

- CI/CD
- production cloud deployment
- monitoring and drift detection
- automated retraining
- automatic production promotion without evaluation

Those belong to later lifecycle phases.
