# Machine Learning

## Overview

The machine-learning component of the Building & Energy Intelligence Platform is designed as a forecasting pipeline for short-horizon building energy consumption.

The ML workflow currently consists of:

```text
BDG2 Data
   ↓
Validation
   ↓
Feature Engineering
   ↓
Baseline / Model Training
   ↓
Evaluation
   ↓
Model Artifact
   ↓
FastAPI Inference Service
````

The current implementation establishes the first complete path from a processed dataset to a served ML prediction.

---

# Dataset

The initial ML pipeline uses Building Data Genome Project 2 (BDG2).

The dataset provides:

* building metadata
* electricity consumption
* weather information
* hourly observations

The current project uses a selected subset of 12 buildings for the initial development pipeline.

The canonical processed feature dataset is:

```text
data/processed/phase1_features.parquet
```

Current dataset size:

```text
Rows:    210,528
Columns: 44
Buildings: 12
```

---

# Prediction Target

The primary prediction target is:

```text
target_next_hour_kwh
```

The task is therefore a one-hour-ahead energy-consumption forecasting problem.

Conceptually:

```text
Historical Building Context
        +
Weather / Metadata
        ↓
Predict next-hour energy consumption
```

---

# Feature Engineering

The Phase 1 feature pipeline constructs features from historical consumption, weather, building metadata, and temporal information.

Feature categories include:

### Historical Energy

* lagged energy consumption
* rolling energy statistics
* recent consumption patterns

### Rolling Statistics

Examples include:

* rolling means
* rolling maximums

These provide information about recent building energy behavior.

### Weather

Weather-related features are included to provide environmental context.

### Building Metadata

The feature set incorporates building-level information such as:

* floor area
* primary use
* site information
* timezone

### Calendar Features

Temporal features capture recurring patterns such as:

* hour
* day
* weekday
* month
* calendar-related behavior

### Degree-Day Features

Heating and cooling degree-day style features are included to represent temperature-related building demand.

---

# Feature / Inference Parity

The inference service must reproduce the feature construction expected by the trained model.

The current prediction path is:

```text
168-hour history
      ↓
Inference feature construction
      ↓
Feature vector
      ↓
Random Forest
      ↓
Prediction
```

The inference implementation is intentionally aligned with the Phase 1 feature definitions.

This prevents the application from creating an incompatible feature representation at prediction time.

---

# Baseline Models

Phase 1 evaluated multiple approaches.

The primary benchmark was persistence.

Persistence predicts the next hour using the most recent observed energy value.

Conceptually:

```text
Prediction(t + 1) = Energy(t)
```

This is intentionally simple but provides an important benchmark for determining whether learned models add value.

---

# Phase 1 Model Comparison

The main test-set results were:

| Model         | Test NMAE |  Test MAE | Test RMSE | Test CVRMSE | Macro Building NMAE |
| ------------- | --------: | --------: | --------: | ----------: | ------------------: |
| Persistence   |  0.059274 |  8.444619 | 23.639729 |  16.593072% |            0.094865 |
| Random Forest |  0.076385 | 10.873100 | 24.717749 |  17.364619% |            0.137032 |

Additional Phase 1 experiments included Ridge Regression and HistGradientBoosting.

The key conclusion was that the persistence benchmark outperformed the evaluated learned models on the Phase 1 test evaluation.

---

# Champion and Challenger

The Phase 1 results establish an important distinction.

```text
Benchmark Champion
        ↓
Persistence

Learned Model / Initial Challenger
        ↓
Random Forest
```

Persistence is therefore the strongest Phase 1 benchmark.

Random Forest is retained as the first learned model used by the inference service.

The Random Forest model should not be described as the Phase 1 overall performance champion.

---

# Random Forest Artifact

The current Random Forest artifact is:

```text
models/random_forest_phase1.joblib
```

The artifact contains the information required by the inference service, including:

* model name
* trained model
* feature columns
* metadata

The model loader validates the expected artifact structure before making the service ready.

---

# Model Version

The current model reports:

```text
model_name:
random_forest

model_version:
phase1
```

This information is returned with predictions.

The explicit version field provides a foundation for future model lifecycle management.

Later phases will extend this concept with proper experiment tracking, model registration, candidate models, and promotion.

---

# Inference Contract

The FastAPI inference service currently requires:

```text
Building metadata
+
Weather context
+
Target timestamp
+
168 consecutive hourly historical observations
```

The historical observations must satisfy the service's validation requirements.

The service validates:

* timestamps
* energy values
* ordering
* duplicates
* required history length

Only after validation does feature construction and inference occur.

---

# ML Service Architecture

The trained model is exposed through a standalone FastAPI service.

Location:

```text
apps/model_service/
```

The primary endpoints are:

```text
GET  /health
GET  /ready
POST /predict
```

The prediction flow is:

```text
Prediction Request
       ↓
Pydantic Validation
       ↓
Historical Context Validation
       ↓
Feature Construction
       ↓
Random Forest
       ↓
Prediction Response
```

---

# Application Integration

The ML service is not called directly by the frontend.

The current application architecture is:

```text
Next.js / React
       ↓
Node.js / Express
       ↓
FastAPI
       ↓
Random Forest
```

The Express prediction service prepares the application-level prediction request and forwards it to FastAPI.

This keeps model-specific implementation details inside the ML service.

---

# Current Prediction Example

A successful inference returns a structured response containing:

```text
building_id
timestamp
predicted_energy_kwh
model_name
model_version
```

For example, conceptually:

```json
{
  "building_id": "Bear_assembly_Angel",
  "timestamp": "2017-12-31T23:00:00Z",
  "predicted_energy_kwh": 253.7778,
  "model_name": "random_forest",
  "model_version": "phase1"
}
```

---

# Error Analysis

Phase 1 included comparison of Random Forest against persistence across different conditions.

The analysis showed that Random Forest improved over persistence for some buildings and periods, but persistence remained stronger overall.

Persistence also remained stronger across the evaluated monthly and weekday/weekend comparisons.

These results reinforce the importance of benchmarking learned models against simple baselines.

The project therefore avoids claiming that a more complex model is automatically better.

---

# Important Forecasting Limitation

The current BDG2 dataset ends on:

```text
2017-12-31
```

Therefore, the current application forecast endpoint demonstrates model inference using historical data.

It is not a live forecast of present-day building consumption.

The current architecture should be understood as:

```text
Historical Dataset
        ↓
Historical Context
        ↓
Model Inference
        ↓
Demonstration Prediction
```

rather than:

```text
Live Building
        ↓
Real-Time Sensors
        ↓
Production Forecast
```

A genuine live forecasting system would require continuously arriving operational data.

---

# Current ML Scope

The completed ML scope includes:

* BDG2 ingestion
* data validation
* feature engineering
* historical feature construction
* baseline benchmarking
* model comparison
* Random Forest training
* model evaluation
* model serialization
* model loading
* inference validation
* FastAPI model serving
* application-level forecast integration

---

# Not Yet Implemented

The following ML/MLOps capabilities are intentionally deferred:

* experiment tracking
* formal model registry
* automated model promotion
* production champion management
* feature store
* online feature serving
* data drift monitoring
* prediction monitoring
* automated performance monitoring
* automated retraining
* retraining triggers
* CI/CD model deployment
* cloud deployment

These belong to later project phases.

---

# Future ML Lifecycle

The intended future lifecycle is:

```text
Data
 ↓
Feature Engineering
 ↓
Experiment
 ↓
Training
 ↓
Evaluation
 ↓
Candidate Model
 ↓
Registry
 ↓
Promotion Gate
 ↓
Champion
 ↓
Inference
 ↓
Monitoring
 ↓
Drift / Performance Detection
 ↓
Retraining
 ↓
Candidate Model
```

The important design principle is that retraining and promotion are controlled processes.

A newly trained model should not automatically replace the current production model simply because it is newer.

---

# Future Model Evaluation

Future model promotion should consider more than a single aggregate metric.

Potential evaluation dimensions include:

* overall forecasting error
* building-level performance
* temporal performance
* comparison against persistence
* stability across evaluation periods
* degradation or improvement relative to the current champion

The exact promotion criteria will be defined during the MLOps/model-lifecycle phase.

---

# Current ML Architecture Summary

```text
                 ┌─────────────────────┐
                 │     BDG2 Dataset    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Feature Engineering │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Model Evaluation    │
                 │                     │
                 │ Persistence         │
                 │ Random Forest       │
                 │ Ridge               │
                 │ HistGradientBoosting│
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Random Forest       │
                 │ Phase 1 Artifact    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ FastAPI Inference   │
                 │ Service             │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Express Application  │
                 │ API                 │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Next.js Application │
                 └─────────────────────┘
```

The current ML layer is therefore complete enough to support an end-to-end application while remaining deliberately separate from the MLOps infrastructure planned for subsequent phases.
## Phase 4 ML Lifecycle

Phase 4 moved the trained models from local artifacts into an explicit ML lifecycle.

### Registered models

MLflow contains three registered versions:

- v1 � Ridge
- v2 � Random Forest
- v3 � HistGradientBoosting

All three versions have verified MLflow input signatures.

### Evaluation-driven promotion

The best learned model is selected using validation macro-building NMAE.

The persistence baseline is evaluated using the same metric before promotion.

A candidate is rejected when it does not beat the baseline.

Current result:

- Persistence baseline remains the serving strategy.
- Random Forest is the strongest learned model under the learned-model comparison, but it does not pass the baseline guard.
- No learned model currently receives the `@production` alias.

### Serving modes

The model service supports two conceptual modes:

`learned`

A registered MLflow model is loaded through the production alias.

`baseline`

The persistence baseline is served when no valid production model is available.

This distinction keeps model evaluation and deployment decisions separate.

### Inference contract

The inference service builds the same feature family used during training from the supplied building metadata, weather context and historical energy observations.

MLflow signatures were verified against the registered models to confirm compatibility with this feature contract.
