# System Architecture

## Overview

Building & Energy Intelligence is a machine-learning platform for building
energy forecasting and lifecycle management.

The system is designed as a set of independent layers so that data
engineering, machine learning, model inference, application logic, frontend
presentation, and deployment can evolve independently.

The intended high-level architecture is:

```text
                    ┌─────────────────────┐
                    │     React Web UI    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Node / Express    │
                    │   Application API   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI ML        │
                    │   Inference Service │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Model Artifact   │
                    │ / Model Registry    │
                    └─────────────────────┘
````

The offline machine-learning lifecycle is separate from the online
application path:

```text
Raw Data
   ↓
Ingestion
   ↓
Validation
   ↓
Feature Engineering
   ↓
Training
   ↓
Evaluation
   ↓
Model Selection
   ↓
Model Artifact
   ↓
Inference Service
   ↓
Application
   ↓
Monitoring
   ↓
Controlled Retraining
```

## Architectural Goals

The architecture is designed around the following goals:

* separation of concerns
* reproducibility
* testability
* explicit service contracts
* prevention of data leakage
* model/version traceability
* CPU-first local development
* independent evolution of ML and application layers

The system should remain understandable and runnable on a normal development
laptop before introducing deployment infrastructure.

## Repository Architecture

```text
building-energy-intelligence/
├── apps/
│   ├── web/
│   ├── api/
│   └── model_service/
├── ml/
│   ├── ingestion/
│   ├── validation/
│   ├── features/
│   ├── training/
│   ├── evaluation/
│   ├── monitoring/
│   └── artifacts/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data/
├── configs/
├── scripts/
├── docker/
├── .github/workflows/
├── docs/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── reference/
├── models/
├── reports/
└── notebooks/
```

## Component Responsibilities

### `ml/`

The `ml/` directory contains the machine-learning lifecycle.

Responsibilities include:

* data ingestion
* data validation
* feature engineering
* model training
* model evaluation
* monitoring
* model lifecycle logic

The ML layer should not depend on the frontend.

### `apps/model_service/`

The `apps/model_service/` directory contains the standalone ML inference
service.

Responsibilities include:

* loading model artifacts
* validating prediction requests
* reconstructing model features
* running inference
* returning structured prediction responses
* exposing health/readiness endpoints
* logging inference activity

The service provides an HTTP boundary around the trained model.

The service should not contain the complete model-training pipeline.

### `apps/api/`

The `apps/api/` directory is reserved for the future application backend.

Its responsibilities will include:

* application/business logic
* application-level API contracts
* persistence
* authentication
* building management
* communication with the ML service
* orchestration of user-facing workflows

The application backend should communicate with the ML service through its
HTTP API rather than importing the ML service's internal implementation.

### `apps/web/`

The `apps/web/` directory is reserved for the future web dashboard.

Its responsibilities will include:

* building overview
* energy consumption visualization
* historical trends
* predictions
* prediction versus actual views
* building comparisons
* model information
* system health
* monitoring information
* lifecycle controls

The frontend should communicate with the application backend rather than
directly depending on the ML implementation.

## Offline ML Architecture

The offline ML pipeline transforms raw building data into a validated model
artifact.

```text
                    ┌─────────────────┐
                    │    Raw Data     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Ingestion    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Validation   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Feature         │
                    │ Engineering     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Temporal Split  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Training     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Evaluation    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Model Selection │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Model Artifact  │
                    └─────────────────┘
```

The resulting model artifact becomes the input to the inference service.

## Online Inference Architecture

The current Phase 2 service implements the following path:

```text
Client
  ↓
HTTP POST /predict
  ↓
Pydantic Request Validation
  ↓
Inference Service
  ↓
Feature Reconstruction
  ↓
Loaded Model
  ↓
Prediction
  ↓
Prediction Response
```

The service also exposes:

```text
GET /health
GET /ready
POST /predict
```

FastAPI provides the OpenAPI/Swagger interface for the service.

## Model Loading

The model service loads the model artifact during application startup.

The model is loaded once and retained for the service lifetime.

The service validates that the artifact contains the expected structure,
including:

* model name
* model object
* feature columns
* metadata

The service exposes model identity through the readiness response and
prediction response.

This allows downstream systems to determine which model version produced a
prediction.

## Feature Contract

The model requires a specific feature set.

The inference service reconstructs the same feature representation used during
training.

Features include:

* building metadata
* weather variables
* calendar features
* cyclical time features
* historical energy lags
* rolling energy statistics
* degree-day features

Historical features must only use information available before the prediction
timestamp.

A dedicated feature-parity test verifies that the inference feature
construction remains consistent with the Phase 1 feature builder.

## Data Leakage Prevention

The forecasting target represents the next hourly energy value.

Therefore, information from the prediction interval must not be included in
the input features.

Rolling energy features are calculated from strictly past observations.

The feature pipeline uses a one-step shift before rolling calculations so that
the current interval cannot leak into its own prediction.

This rule applies both to offline feature construction and online inference.

## API Boundary

The ML service uses explicit request and response schemas.

A prediction request contains:

* building identifier
* prediction timestamp
* site/building metadata
* weather information
* historical energy observations

The current Random Forest requires 168 hours of historical observations because
its feature set contains lag and rolling features extending to 168 hours.

The service validates the historical observations for:

* sufficient length
* unique timestamps
* chronological ordering
* consecutive hourly intervals
* immediate adjacency to the prediction timestamp

Invalid requests are rejected before model inference.

## Error Handling

The service distinguishes between different classes of failure.

### Invalid request

Malformed or invalid input is rejected with an HTTP validation error.

### Service not ready

If the model has not been loaded, the readiness and prediction boundaries
return a service-unavailable response.

### Inference validation failure

Invalid historical data that passes basic schema validation but fails temporal
feature requirements is rejected with a client error.

### Unexpected inference failure

Unexpected internal failures are logged while the API returns a controlled
error response instead of exposing internal stack traces.

### Model artifact failure

Missing or invalid model artifacts prevent the model from becoming ready.

The model loader normalizes low-level artifact-loading failures into a
predictable application-level error.

## Testing Architecture

Testing is performed at multiple levels.

```text
Unit Tests
    ↓
Feature / Validation / Metrics / Inference
    ↓
Contract Tests
    ↓
API Schemas / Feature Parity
    ↓
Service Tests
    ↓
Health / Readiness / Real Model Prediction
```

The Phase 2 service has been verified with the actual Phase 1 Random Forest
artifact.

The current test suite contains 20 passing tests, including an automated test
that sends a prediction request through the actual `/predict` endpoint.

## Current Implemented Architecture

At the end of Phase 2, the implemented system boundary is:

```text
                Phase 1
            Model Artifact
                  │
                  ▼
        ┌─────────────────────┐
        │     ModelLoader     │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │   FastAPI ML        │
        │   Model Service     │
        ├─────────────────────┤
        │                     │
        │ GET  /health        │
        │ GET  /ready         │
        │ POST /predict       │
        │                     │
        └─────────────────────┘
```

The Phase 1 Random Forest artifact is currently served through this boundary.

The frontend and application backend have not yet been implemented.

## Future Application Architecture

Once the application backend and frontend are implemented, the online path will
become:

```text
                         ┌───────────────┐
                         │   React Web   │
                         │      UI       │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │ Node/Express  │
                         │ Application   │
                         │     API       │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │   FastAPI ML  │
                         │    Service    │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │ Model Artifact│
                         └───────────────┘
```

This separation allows the ML service to evolve independently from the
application interface.

## Future ML Lifecycle Architecture

Later phases will extend the system from static model serving to a complete
ML lifecycle:

```text
Production Data
      ↓
Data Validation
      ↓
Feature Processing
      ↓
Prediction
      ↓
Monitoring
      ↓
Performance / Drift Detection
      ↓
Retraining Candidate
      ↓
Evaluation
      ↓
Champion / Challenger Comparison
      ↓
Model Promotion
      ↓
New Model Version
      ↓
Inference Service
```

Retraining and model promotion should be controlled by evaluation results
rather than automatically replacing the current champion.

## Future Infrastructure

Infrastructure will be introduced incrementally after the application
architecture is stable.

Planned capabilities include:

* Docker
* Docker Compose
* experiment tracking
* model versioning
* CI/CD
* service monitoring
* data monitoring
* model monitoring
* drift detection
* controlled retraining
* deployment

These components are intentionally not part of the current Phase 2
implementation.