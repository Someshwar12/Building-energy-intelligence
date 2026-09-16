# Phase 4 — Completion Report

## 1. Phase Objective

Phase 4 introduced reproducible local infrastructure and explicit ML lifecycle management around the existing Building & Energy Intelligence forecasting system.

The objectives were to:

- Containerize the application.
- Introduce MLflow for experiment tracking.
- Introduce MLflow Model Registry for model versioning.
- Establish an evaluation-driven model lifecycle.
- Prevent weaker learned models from being promoted over the persistence baseline.
- Connect the model service to the MLflow lifecycle.
- Provide a safe baseline-serving mode when no learned model qualifies for production.
- Validate registered model signatures.
- Expose model lifecycle information through the application.
- Verify the complete system through automated tests and runtime checks.

Phase 4 therefore extends the project from:

```text
ML Experiment
````

toward:

```text
Tracked Experiment
        ↓
Registered Model
        ↓
Evaluated Candidate
        ↓
Promotion Decision
        ↓
Controlled Serving
```

---

## 2. Delivered Components

Phase 4 delivered the following components:

* Dockerized Next.js web application.
* Dockerized Node/Express API.
* Dockerized FastAPI model service.
* Dockerized MLflow server.
* Docker Compose orchestration.
* Persistent MLflow storage through a Docker volume.
* MLflow experiment tracking.
* MLflow Model Registry.
* Versioned registered models.
* Candidate evaluation and lifecycle metadata.
* Baseline-aware promotion guard.
* Rejected candidate state.
* Persistence baseline fallback serving.
* MLflow model signature verification.
* Model Lab lifecycle observability.
* Runtime health and readiness endpoints.
* End-to-end prediction verification.
* Reproducibility metadata associated with training runs.
* Expanded model-service tests.
* Local containerized runtime verification.

---

## 3. Final Docker Architecture

The local application is composed of four services:

```text
                     ┌──────────────────────┐
                     │      Next.js Web      │
                     │        :3000         │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │    Node / Express    │
                     │        :4000         │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │   FastAPI Model      │
                     │      Service :8000   │
                     └──────────┬───────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │       MLflow         │
                     │        :5000         │
                     │ Tracking + Registry  │
                     └──────────────────────┘
```

Docker Compose provides:

* service orchestration
* internal service networking
* environment configuration
* persistent MLflow storage
* reproducible local startup

The browser communicates with the host API at:

```text
http://localhost:4000
```

The Express API communicates with FastAPI through the Compose network:

```text
http://model-service:8000
```

The model service communicates with MLflow through:

```text
http://mlflow:5000
```

The MLflow server uses the persistent Docker volume:

```text
mlflow-data
```

---

## 4. Container Responsibilities

Each container has a focused responsibility.

### Web

The web container runs the Next.js application.

```text
Port: 3000
```

It is responsible for:

* dashboard rendering
* building views
* consumption visualization
* forecast visualization
* anomaly visualization
* Model Lab
* application interaction

It does not directly load MLflow models.

---

### API

The API container runs the Node/Express application.

```text
Port: 4000
```

It is responsible for:

* application API routes
* building data access
* historical consumption access
* forecast orchestration
* anomaly analysis access
* Model Lab API access

The API acts as the application boundary between the frontend and backend services.

---

### Model Service

The model-service container runs FastAPI.

```text
Port: 8000
```

It is responsible for:

* prediction request validation
* historical context validation
* inference feature construction
* model loading
* serving-mode selection
* prediction generation
* model identity reporting
* readiness state

---

### MLflow

The MLflow container provides:

```text
Port: 5000
```

It is responsible for:

* experiment tracking
* run metadata
* model artifacts
* registered model versions
* model lifecycle metadata
* aliases

MLflow storage is persisted through:

```text
mlflow-data
```

---

## 5. MLflow Experiment Tracking

MLflow was introduced as the experiment-tracking layer for the forecasting pipeline.

The primary experiment is:

```text
building-energy-phase1
```

Training runs record relevant experiment information including:

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
* lifecycle metadata where applicable

The resulting relationship is:

```text
Training Configuration
        ↓
Training Run
        ↓
Parameters
Metrics
Tags
Artifacts
Reproducibility Metadata
        ↓
Registered Model
```

This provides traceability between the trained model, its evaluation results, configuration, and source state.

---

## 6. Model Registry

The registered MLflow model is:

```text
building-energy-forecast
```

The current registry contains three learned-model versions:

| Version | Model                | Lifecycle State |
| ------- | -------------------- | --------------- |
| v1      | Ridge                | Evaluated       |
| v2      | Random Forest        | Rejected        |
| v3      | HistGradientBoosting | Evaluated       |

All three registered versions have verified MLflow input signatures.

Version v2 contains explicit rejection metadata documenting that the candidate failed the baseline guard.

No learned model currently has the:

```text
@production
```

alias.

This is intentional.

The absence of a production learned model is a valid lifecycle state because the persistence baseline remains available for serving.

---

## 7. Evaluation-Driven Promotion Policy

The promotion workflow does not automatically promote the strongest learned model.

The process is:

```text
Training
   ↓
MLflow Experiment
   ↓
Evaluation
   ↓
Select Best Evaluated Learned Candidate
   ↓
Compare Against Persistence Baseline
   ↓
Baseline Guard
   ↓
┌─────────────────────────────┐
│ Does candidate beat baseline?│
└──────────────┬──────────────┘
               │
      ┌────────┴────────┐
      │                 │
     PASS              FAIL
      │                 │
      ▼                 ▼
Eligible            Reject Candidate
for Production          │
      │                 │
      ▼                 ▼
@production       Preserve Baseline
```

The current learned-model selection metric is:

```text
validation_macro_building_nmae
```

The promotion decision must use the appropriate baseline comparison for the same evaluation criterion.

The purpose of this guard is to prevent a learned model from being promoted simply because it performs better than other learned models.

---

## 8. Current Model Evaluation State

The Phase 1 learned-model results are:

| Model                | Validation MAE | Validation NMAE | Validation Macro Building NMAE |
| -------------------- | -------------: | --------------: | -----------------------------: |
| Random Forest        |      11.585128 |        0.082228 |                       0.127556 |
| HistGradientBoosting |      12.014662 |        0.085277 |                       0.355616 |
| Ridge                |      16.439043 |        0.116680 |                       4.065300 |

Under the current learned-model comparison:

```text
Random Forest
```

is the strongest evaluated learned candidate based on validation macro-building NMAE.

However, the persistence baseline remains stronger under the baseline comparison used for the promotion decision.

Therefore:

```text
Production learned model:
None

Current serving strategy:
Persistence baseline
```

The system does not artificially assign a production alias to a learned model simply because a learned candidate exists.

---

## 9. Baseline Strategy

The primary baseline is persistence.

Persistence uses the most recent observed energy value as the next-hour prediction.

Conceptually:

```text
Prediction(t + 1) = Energy(t)
```

The project also evaluates:

```text
pred_previous_day
pred_previous_week
```

The baseline results are stored in:

```text
reports/generated/phase1_baseline_results.csv
```

The persistence baseline is represented as:

```text
pred_persistence
```

and displayed in the application as:

```text
Persistence
```

The baseline is kept conceptually separate from the learned-model registry.

---

## 10. Baseline-Aware Model Lifecycle

The current lifecycle distinguishes between:

```text
Learned Models
```

and:

```text
Baseline Strategies
```

The learned-model path is:

```text
Ridge
Random Forest
HistGradientBoosting
        ↓
Evaluation
        ↓
Candidate Selection
        ↓
Baseline Guard
```

The baseline path is:

```text
Persistence
        ↓
Benchmark
        ↓
Fallback Serving
```

The two paths meet at the promotion decision.

This prevents the registry from treating a simple baseline strategy as if it were an ordinary learned model.

---

## 11. Current Production Decision

The current lifecycle state is:

```text
Learned Models
      ↓
Evaluated
      ↓
Best learned candidate selected
      ↓
Baseline comparison
      ↓
Baseline guard failed
      ↓
No learned production alias
      ↓
Persistence remains operational
```

The current serving strategy is therefore:

```text
model_name    = persistence
model_version = baseline
serving_mode  = baseline
```

The application exposes this serving state so that a baseline prediction is not presented as though it came from a learned production model.

---

## 12. Serving Modes

The model service supports two conceptual serving modes.

### Learned Mode

A valid registered MLflow model is loaded through the configured production alias.

```text
serving_mode = learned
```

The flow is:

```text
MLflow @production
        ↓
Registered Model
        ↓
Model Loader
        ↓
Feature Vector
        ↓
Prediction
```

---

### Baseline Mode

When no valid learned production model is available, the service serves the persistence baseline.

```text
serving_mode = baseline
```

The flow is:

```text
Latest Historical Energy
        ↓
Persistence Prediction
```

This allows the application to remain operational while preserving the evaluation policy.

---

## 13. Baseline Fallback Safety

The persistence fallback was implemented as an explicit serving mode rather than silently pretending that a learned model is available.

When baseline mode is active:

```text
model_name    = persistence
model_version = baseline
```

The inference service uses the latest observed energy value from the supplied history.

This creates a safe operational path:

```text
No qualifying learned model
          ↓
No forced promotion
          ↓
Persistence fallback
          ↓
Prediction service remains available
```

The fallback is therefore part of the ML lifecycle rather than an unrelated hard-coded prediction path.

---

## 14. MLflow Model Signature Verification

The registered models were verified directly against the Docker-hosted MLflow server.

Versions:

```text
v1
v2
v3
```

all expose valid MLflow input signatures.

The signature contains the forecasting feature contract, including categories such as:

* building identifiers
* site information
* primary use
* building area
* weather variables
* calendar features
* time features
* historical lag features
* rolling energy features
* heating degree-hour features
* cooling degree-hour features

The registered models expose compatible input contracts for the serving pipeline.

The output is a floating-point prediction vector.

Signature verification provides an additional check that registered artifacts retain the expected model-input contract.

---

## 15. Inference Contract

The FastAPI prediction service requires:

```text
Building Metadata
+
Weather Context
+
Target Timestamp
+
168 Consecutive Hourly Historical Observations
```

The historical observations must satisfy the service validation requirements.

The service validates:

* timestamp structure
* energy values
* chronological ordering
* duplicate timestamps
* required history length

Only after validation does feature construction occur.

The prediction flow is:

```text
Prediction Request
        ↓
Pydantic Validation
        ↓
Historical Context Validation
        ↓
Inference Feature Construction
        ↓
Serving Mode
        ↓
Learned Model / Persistence
        ↓
Prediction Response
```

---

## 16. Feature / Inference Parity

The inference service reconstructs the feature representation required by the trained model.

The serving path is:

```text
168-hour History
      ↓
Historical Feature Construction
      ↓
Weather + Building Context
      ↓
Model Feature Vector
      ↓
Registered Model
      ↓
Prediction
```

This preserves the feature semantics established during Phase 1.

The model service does not require the frontend to construct the internal ML feature vector.

This keeps feature engineering behind the ML-service boundary.

---

## 17. Model-Service Architecture

The model service is located at:

```text
apps/model_service/
```

Primary endpoints:

```text
GET  /health
GET  /ready
POST /predict
```

The service is responsible for:

* loading the serving strategy
* validating prediction requests
* reconstructing inference features
* serving learned models through MLflow
* serving the persistence baseline when required
* returning model identity
* exposing health and readiness state

The service is deliberately independent from the Next.js frontend.

---

## 18. Application Integration

The ML service is not called directly by the frontend.

The application architecture is:

```text
Next.js / React
       ↓
Node.js / Express
       ↓
FastAPI
       ↓
MLflow Model / Persistence Baseline
```

The Express API prepares the application-level prediction request and forwards it to FastAPI.

This keeps model-specific implementation details inside the model service.

The frontend therefore consumes an application API rather than accessing:

* MLflow
* model artifacts
* Python code
* internal feature-construction logic

directly.

---

## 19. Model Lab

Phase 4 also introduced application-level visibility into the ML lifecycle through the Model Lab.

The Model Lab exposes:

* current serving strategy
* production model state
* candidate state
* registered model versions
* evaluated versions
* rejected versions
* model families
* MLflow run metadata
* model metrics
* model parameters
* lifecycle metadata
* baseline metrics
* baseline strategies
* promotion metadata

The Model Lab separates:

```text
Learned Model Registry
```

from:

```text
Persistence Baseline
```

so that the UI does not imply that every benchmark is a registered learned model.

---

## 20. Registered Model Lifecycle Metadata

Registered model versions contain lifecycle information including:

```text
model_family
validation_status
lifecycle_status
promotion_metric
promotion_reason
baseline_guard
baseline_model
baseline reference information
rejection_reason
```

This allows the application to distinguish between:

```text
Evaluated
Candidate
Rejected
Production
```

rather than treating every registered model version as equivalent.

The rejected Random Forest version remains visible as lifecycle history instead of being deleted.

---

## 21. Rejected Candidate State

The Random Forest candidate is currently recorded as rejected because it did not pass the baseline guard.

The lifecycle concept is:

```text
Random Forest
      ↓
Evaluated
      ↓
Best learned candidate
      ↓
Baseline comparison
      ↓
Guard failed
      ↓
Rejected
```

The candidate remains registered so that:

* its run remains traceable
* its metrics remain inspectable
* its parameters remain available
* the lifecycle decision remains auditable

Rejection does not mean the artifact is deleted.

---

## 22. Reproducibility

Phase 4 establishes a reproducible local execution environment.

The system can be started through Docker Compose with explicit services for:

```text
Web
API
Model Service
MLflow
```

MLflow persistence is provided through:

```text
mlflow-data
```

Training records relevant experiment and model metadata in MLflow.

Git provides source-version traceability.

The model registry provides versioned model artifacts and lifecycle metadata.

Together:

```text
Git
+
Dataset / Configuration
+
MLflow Run
+
Model Artifact
+
Model Version
+
Lifecycle Metadata
```

provide the foundation for reproducible experimentation and controlled model serving.

---

## 23. Model-Service Container Design

The model-service container is intentionally focused.

When operating through the MLflow lifecycle, it does not need to bundle the complete local dataset or the complete local model directory.

Instead:

```text
Model Service
      ↓
MLflow
      ↓
Registered Model
```

The image contains the application and ML code required to perform inference and communicate with MLflow.

This keeps the serving image aligned with its actual responsibility.

---

## 24. Runtime Verification

The Docker Compose runtime was verified with the four application services:

```text
Web              : 3000
API              : 4000
Model Service    : 8000
MLflow           : 5000
```

The expected service topology was successfully exercised.

The model service was able to initialize its serving state.

The application API was able to communicate with the model service through the Compose network.

The web application was able to consume the API.

---

## 25. Model Service Health Verification

The model service exposes:

```text
GET /health
```

The endpoint verifies service health.

The service also exposes:

```text
GET /ready
```

Readiness reports whether the model service has successfully initialized a usable serving strategy.

The readiness state includes model identity and serving mode.

The current expected runtime state is:

```text
status        = ready
model_name    = persistence
model_version = baseline
serving_mode  = baseline
```

---

## 26. API Health Verification

The Node/Express API exposes its health endpoint.

The API health check verifies that the application backend is operational independently of the model service.

The runtime therefore has separate health boundaries:

```text
Web
 ↓
API
 ↓
Model Service
 ↓
MLflow
```

This makes service failures easier to isolate.

---

## 27. End-to-End Prediction Verification

A real prediction request was successfully exercised against the running application stack.

The request contains:

* building metadata
* weather context
* historical energy observations
* prediction timestamp

The request flows through:

```text
Application API
      ↓
FastAPI
      ↓
Request Validation
      ↓
Inference Feature Construction
      ↓
Serving Mode Decision
      ↓
Persistence Baseline
      ↓
Prediction Response
```

A verified runtime response was:

```text
building_id          : Bear_assembly_Angel
timestamp            : 2017-12-31T23:00:00Z
predicted_energy_kwh : 284.5062
model_name           : persistence
model_version        : baseline
```

The returned prediction correctly reflects the active persistence serving strategy.

This verifies the complete prediction path in the current baseline-serving state.

---

## 28. Automated Test Verification

The model-service changes were validated against the complete existing test suite.

Final result:

```text
20 passed
```

No test failures remained after introducing baseline-safe inference and the related model-service lifecycle changes.

The remaining HTTPX/Starlette messages were deprecation warnings and did not cause test failures.

The test suite therefore provides coverage across the existing ML and service behaviour without requiring the production MLflow server for ordinary unit tests.

---

## 29. Dockerized Runtime Verification

The Dockerized runtime was verified after integrating:

* web container
* API container
* model-service container
* MLflow container
* MLflow persistent storage
* inter-service networking
* MLflow-based model loading
* baseline fallback serving

The architecture is therefore executable as a local multi-service system rather than existing only as disconnected source code.

---

## 30. Data and MLflow Boundary

Phase 4 did not replace the underlying Phase 1 dataset.

The canonical feature dataset remains:

```text
data/processed/phase1_features.parquet
```

Phase 4 adds lifecycle infrastructure around the ML pipeline:

```text
Dataset
   ↓
Feature Engineering
   ↓
Training
   ↓
Evaluation
   ↓
MLflow
   ↓
Model Registry
   ↓
Serving
```

The underlying data pipeline and the model lifecycle remain separate concerns.

---

## 31. Historical Forecasting Limitation

The BDG2 source data ends on:

```text
2017-12-31
```

Therefore, the current application forecast is a historical inference demonstration.

It is not a live forecast of present-day building energy consumption.

The current architecture should be described as:

```text
Historical Dataset
        ↓
Historical Context
        ↓
Inference
        ↓
Prediction
```

rather than:

```text
Live Building
        ↓
Real-Time Telemetry
        ↓
Production Forecast
```

A live operational forecasting system would require continuously arriving building data.

---

## 32. Known Limitations and Deferred Scope

The following capabilities are intentionally outside Phase 4:

* GitHub Actions CI/CD.
* Automated monitoring.
* Automated data-quality monitoring.
* Feature drift detection.
* Prediction-error monitoring.
* Automated performance monitoring.
* Automated retraining.
* Automated retraining triggers.
* Automatic production promotion without evaluation.
* Cloud deployment.
* Kubernetes.
* Large-scale distributed infrastructure.
* Large LLM infrastructure.
* Agent infrastructure.
* Real-time building telemetry ingestion.
* Full operational prediction storage.
* Formal feature-store infrastructure.
* Full production-scale data platform.

These capabilities are deferred until they solve a concrete lifecycle or engineering requirement.

---

## 33. Phase 4 Engineering Decisions

### MLflow is the lifecycle authority

MLflow is used for:

* experiment tracking
* model registration
* model versioning
* model artifacts
* lifecycle metadata
* aliases

The local model directory is not treated as the authoritative production registry.

---

### No Forced Production Model

A learned model is not promoted simply because it is the strongest learned model.

The candidate must satisfy the defined evaluation and baseline requirements.

If no learned model qualifies:

```text
No learned production model
        ↓
Persistence baseline
```

remains operational.

---

### Baseline Remains Operational

The persistence baseline is treated as a legitimate serving strategy.

It is not merely a development-only benchmark.

This allows the service to remain operational without weakening the model-promotion policy.

---

### Rejected Models Remain Traceable

A rejected candidate is retained in MLflow rather than deleted.

This preserves:

* experiment history
* model version
* metrics
* parameters
* lifecycle reasoning

---

### Docker Remains Local-First

Docker Compose provides reproducible infrastructure without prematurely introducing:

* cloud infrastructure
* Kubernetes
* distributed orchestration
* unnecessary operational complexity

---

### Model-Service Image Remains Focused

The model-service image contains the code required for serving and lifecycle interaction.

It does not unnecessarily bundle the complete project dataset or local model directory when operating through MLflow.

---

### Feature Contract Remains Explicit

The inference service reconstructs the model feature representation from the application prediction context.

MLflow signatures provide an additional contract verification mechanism.

---

### Evaluation and Deployment Remain Separate

A model can be:

```text
trained
```

without being:

```text
production
```

A model can be:

```text
registered
```

without being:

```text
production
```

A model can be:

```text
evaluated
```

and still be:

```text
rejected
```

This separation is a core part of the lifecycle design.

---

## 34. Phase 4 Completion Checklist

* [x] Dockerfiles created and integrated.
* [x] Docker Compose configuration operational.
* [x] React/Next.js web container operational.
* [x] Node/Express API container operational.
* [x] FastAPI model-service container operational.
* [x] MLflow container operational.
* [x] Persistent MLflow Docker volume configured.
* [x] MLflow experiment tracking implemented.
* [x] Model Registry implemented.
* [x] Model versions registered.
* [x] Learned-model evaluation implemented.
* [x] Baseline benchmarking implemented.
* [x] Baseline-aware promotion guard implemented.
* [x] Rejected candidate state recorded.
* [x] Persistence baseline fallback serving implemented.
* [x] Health endpoint implemented and verified.
* [x] Readiness endpoint implemented and verified.
* [x] API health verified.
* [x] MLflow model signatures verified.
* [x] End-to-end prediction verified.
* [x] Model Lab lifecycle observability implemented.
* [x] 20/20 automated tests passing.
* [x] Dockerized runtime verified.
* [x] Reproducibility metadata implemented.
* [x] Phase 4 engineering decisions documented.
* [x] Phase 4 completion report created.

---

## 35. Phase 4 Final ML State

The final ML lifecycle is:

```text
BDG2 Data
    ↓
Validation
    ↓
Feature Engineering
    ↓
Training
    ↓
MLflow Experiment Tracking
    ↓
MLflow Model Registry
    ↓
Model Evaluation
    ↓
Best Learned Candidate
    ↓
Baseline Guard
    ↓
┌─────────────────────────┐
│                         │
▼                         ▼
Pass                      Fail
│                         │
▼                         ▼
Production Eligible       Rejected
│                         │
▼                         ▼
@production               Persistence
                          remains serving
```

Current registered learned models:

```text
v1 — Ridge
v2 — Random Forest — Rejected
v3 — HistGradientBoosting
```

Current serving state:

```text
model_name    = persistence
model_version = baseline
serving_mode  = baseline
```

No learned model currently owns:

```text
@production
```

---

## 36. Phase 4 Final System State

The Building & Energy Intelligence Platform now has:

```text
Data
  ↓
Validation
  ↓
Feature Engineering
  ↓
Training
  ↓
MLflow Experiment Tracking
  ↓
MLflow Model Registry
  ↓
Evaluation
  ↓
Baseline Guard
  ↓
Production Decision
  ↓
Model Service
  ↓
Node / Express API
  ↓
Next.js Dashboard
```

The system is no longer only a collection of ML experiments and application components.

It now has an explicit model lifecycle with:

* reproducible local infrastructure
* tracked experiments
* versioned models
* verified model contracts
* evaluation-driven candidate selection
* baseline-aware promotion
* rejected candidate state
* safe baseline fallback
* containerized serving
* health and readiness boundaries
* application-level ML observability
* verified end-to-end inference

---

## 37. Phase 4 Architectural Outcome

The major architectural transition achieved in Phase 4 is:

```text
Before Phase 4

Dataset
   ↓
Training
   ↓
Local Model Artifact
   ↓
FastAPI
   ↓
Application
```

to:

```text
After Phase 4

Dataset
   ↓
Feature Engineering
   ↓
Training
   ↓
MLflow Experiment
   ↓
Registered Model Version
   ↓
Evaluation
   ↓
Baseline Guard
   ↓
Production Decision
   ↓
┌─────────────────────────┐
│ Learned Model            │
│ OR                       │
│ Persistence Baseline     │
└────────────┬────────────┘
             ↓
        FastAPI Service
             ↓
        Express API
             ↓
        Next.js Dashboard
```

This is the core completion outcome of Phase 4.

---

## 38. Phase 5 Entry Point

Phase 4 establishes the infrastructure required for the next lifecycle layer.

Phase 5 will focus on:

```text
Quality Gates
      ↓
Continuous Testing
      ↓
CI
      ↓
Data Quality Monitoring
      ↓
Drift Detection
      ↓
Prediction Monitoring
      ↓
Performance Detection
      ↓
Controlled Retraining
      ↓
Candidate Evaluation
      ↓
Baseline / Production Guard
      ↓
Controlled Promotion
```

# PHASE 4 — COMPLETE