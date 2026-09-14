# Phase 2 — ML Inference Service

## Objective

Phase 2 converts the Phase 1 machine-learning artifact into a standalone
FastAPI inference service.

The service is intentionally independent from the future application backend.
The eventual architecture is:

React → Node/Express API → FastAPI ML Service → Model

Phase 2 implements only the ML service boundary.

## Implemented Components

### Model loading

`apps/model_service/app/model_loader.py`

- Loads the Phase 1 Random Forest artifact at service startup.
- Loads the model once for the service lifetime.
- Validates the expected artifact structure.
- Exposes model name, version, metadata, and feature columns.
- Normalizes invalid artifact failures into a predictable application error.

### Request validation

`apps/model_service/app/schemas.py`

Prediction requests require:

- building identifier
- timestamp
- building/site metadata
- weather information
- 168 historical hourly energy observations

Historical observations must:

- contain unique timestamps
- be chronologically ordered
- contain exactly the 168 consecutive hours immediately preceding
  the prediction timestamp

Invalid requests are rejected before inference.

### Feature construction

`apps/model_service/app/inference.py`

The service reconstructs the features expected by the Phase 1 model:

- calendar features
- cyclical time features
- energy lags
- rolling energy statistics
- weather features
- heating degree hour
- cooling degree hour

Rolling features use strictly past observations to prevent target leakage.

A dedicated feature-parity test verifies that API feature construction matches
the Phase 1 feature builder.

### HTTP endpoints

#### `GET /health`

Confirms that the service process is alive.

#### `GET /ready`

Confirms that the service has successfully loaded the model.

Returns the loaded model name and version.

#### `POST /predict`

Accepts a validated prediction request and returns:

- building ID
- prediction timestamp
- predicted energy consumption
- model name
- model version

FastAPI also exposes the OpenAPI/Swagger interface at `/docs`.

## Testing

The project contains 20 automated tests covering:

- feature engineering
- data validation
- train/validation/test splitting
- evaluation metrics
- inference
- API schemas
- feature parity
- health/readiness
- real model prediction
- invalid request handling
- model-loader failure handling

Final verification:

- Ruff: all checks passed
- Pytest: 20/20 tests passed

## End-to-End Verification

The actual Phase 1 Random Forest artifact was served through FastAPI.

A real HTTP request produced:

- building: `Bear_assembly_Angel`
- model: `random_forest`
- version: `phase1`
- prediction: approximately `163.48 kWh`

This verifies the complete serving path:

HTTP request
→ Pydantic validation
→ feature construction
→ Phase 1 model
→ prediction
→ structured JSON response

## Architectural Boundary

Phase 2 does not implement:

- React frontend
- Node/Express application backend
- Docker
- MLflow
- CI/CD
- monitoring
- drift detection
- automated retraining
- cloud deployment

Those are intentionally reserved for later phases.

## Phase 2 Outcome

Phase 2 establishes a standalone, testable ML inference service that can serve
the Phase 1 model through a documented HTTP API.

The service is now ready to become an ML component of the larger
Building & Energy Intelligence Platform.