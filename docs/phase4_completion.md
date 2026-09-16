# Phase 4 — Completion Report

## 1. Phase Objective

Phase 4 introduced reproducible local infrastructure and ML lifecycle management around the existing Building & Energy Intelligence forecasting system.

The objectives were to:

- Containerize the application.
- Introduce MLflow for experiment tracking.
- Introduce MLflow Model Registry for model versioning.
- Establish an evaluation-driven model promotion workflow.
- Prevent weaker learned models from being promoted over the persistence baseline.
- Connect the model service to the MLflow lifecycle.
- Provide a safe baseline-serving mode when no learned model qualifies for production.
- Verify the complete system through automated tests and end-to-end runtime checks.

---

## 2. Delivered Components

Phase 4 delivered the following components:

- Dockerized web application.
- Dockerized Node/Express API.
- Dockerized FastAPI model service.
- Dockerized MLflow server.
- Docker Compose orchestration.
- Persistent MLflow storage through a Docker volume.
- MLflow experiment tracking.
- MLflow Model Registry.
- Versioned registered models.
- Candidate evaluation and promotion logic.
- Baseline-aware promotion guard.
- Baseline fallback serving.
- MLflow model signature verification.
- End-to-end prediction verification.
- Runtime health and readiness endpoints.
- Reproducibility metadata associated with training runs.

---

## 3. Final Docker Architecture

The local application is composed of four services:

```text
                    ┌──────────────────┐
                    │    React / Web   │
                    │      :3000       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Node / API     │
                    │      :4000       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ FastAPI Model    │
                    │    Service :8000 │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │     MLflow       │
                    │      :5000       │
                    │ Registry/Tracking│
                    └──────────────────┘
````

Docker Compose provides the local service network and persistent MLflow storage.

The browser communicates with the host API at:

`http://localhost:4000`

The API communicates with the model service through the Compose network:

`http://model-service:8000`

The model service communicates with MLflow through:

`http://mlflow:5000`

The model-service image does not bundle the local `models/` or dataset directories when operating in MLflow mode. Lifecycle-managed models are retrieved through MLflow instead.

---

## 4. MLflow Experiment Tracking

MLflow was introduced as the experiment tracking layer for the forecasting pipeline.

The Phase 1 training workflow now records relevant experiment information including:

* Model parameters.
* Validation metrics.
* Test metrics.
* Dataset/reference information.
* Configuration.
* Git commit information.
* Model artifacts.
* Model signatures.
* Model-family metadata.
* Validation status.

The primary experiment is:

`building-energy-phase1`

This provides traceability between a trained model, its evaluation results, configuration and source state.

---

## 5. Model Registry

The registered MLflow model is:

`building-energy-forecast`

The current registry contains:

| Version | Model                | Lifecycle state |
| ------- | -------------------- | --------------- |
| v1      | Ridge                | Evaluated       |
| v2      | Random Forest        | Rejected        |
| v3      | HistGradientBoosting | Evaluated       |

All three registered versions are in `READY` state.

Version v2 contains explicit rejection metadata documenting that it failed the baseline guard.

No model currently has the `@production` alias.

This is intentional.

---

## 6. Evaluation-Driven Promotion Policy

The promotion workflow does not automatically promote the best learned model.

The process is:

```text
Training
   ↓
MLflow experiment
   ↓
Evaluation
   ↓
Select best learned candidate
   ↓
Compare against persistence baseline
   ↓
 ┌─────────────────────────────┐
 │ Does candidate beat baseline?│
 └──────────────┬──────────────┘
                │
       ┌────────┴────────┐
       │                 │
      YES                NO
       │                 │
       ▼                 ▼
 production          reject candidate
       │                 │
       ▼                 ▼
 @production       baseline remains
```

The comparison uses the same metric on both sides:

`validation_macro_building_nmae`

This prevents a metric-definition mismatch from producing an invalid promotion decision.

The promotion guard therefore protects against promoting a learned model simply because it performs better than other learned models.

---

## 7. Current Model Evaluation State

The persistence baseline currently performs better than the evaluated learned models on the relevant validation macro-building NMAE metric.

The best learned model under the learned-model comparison is Random Forest, but it does not beat the persistence baseline.

Therefore:

```text
Production learned model:
None

Serving strategy:
Persistence baseline
```

The system does not artificially assign a production alias to a learned model merely to populate the registry.

This is an intentional lifecycle state.

---

## 8. Serving Modes

The model service supports two serving modes.

### Learned mode

A valid MLflow production model is loaded through the configured production alias.

```text
serving_mode = learned
```

### Baseline mode

When no valid production learned model exists, the service serves the persistence baseline.

The current runtime state is:

```text
model_name    = persistence
model_version = baseline
serving_mode  = baseline
```

The persistence prediction uses the most recent observed energy value from the supplied historical observations.

This allows the application to remain operational while preserving the evaluation and promotion policy.

---

## 9. MLflow Model Signature Verification

The registered models were verified directly against the Docker-hosted MLflow server.

Versions v1, v2 and v3 all expose compatible MLflow signatures.

The signature contains the forecasting feature contract, including:

* Building identifiers and metadata.
* Site and primary-use information.
* Building area information.
* Timezone.
* Weather variables.
* Calendar features.
* Cyclical time features.
* Historical energy lag features.
* Rolling energy statistics.
* Heating degree-hour features.
* Cooling degree-hour features.

The model output is a float64 prediction tensor.

The signature verification confirms that the registered model artifacts retain the expected feature contract established by the forecasting pipeline.

---

## 10. End-to-End Verification

A real prediction request was sent to the running FastAPI model service.

The request contained:

* Building metadata.
* Weather context.
* A complete 168-hour energy history.
* A prediction timestamp.

The request successfully passed through:

```text
HTTP request
    ↓
FastAPI request validation
    ↓
InferenceService
    ↓
Serving-mode decision
    ↓
Persistence baseline
    ↓
PredictionResponse
```

The verified response was:

```text
building_id          : Bear_assembly_Angel
timestamp            : 2017-01-08T00:00:00Z
predicted_energy_kwh : 107.0
model_name           : persistence
model_version        : baseline
```

The returned `107.0 kWh` value matched the latest observation supplied in the test history.

This confirms that the inference path operates correctly in the running containerized environment.

---

## 11. Runtime Verification

The Docker Compose stack was successfully started with all four services running:

```text
Web              : 3000
API              : 4000
Model Service    : 8000
MLflow           : 5000
```

Verified endpoints:

### Model service

`GET /health`

Result:

```text
status = ok
service = building-energy-model-service
```

### Model service readiness

`GET /ready`

Result:

```text
status        = ready
model_name    = persistence
model_version = baseline
serving_mode  = baseline
```

### API

`GET /health`

Result:

```text
status = ok
service = building-energy-api
```

MLflow also reported a healthy Docker container.

---

## 12. Automated Test Verification

The model-service changes were validated with the complete existing test suite.

Final result:

```text
20 passed
```

No test failures remained after introducing baseline-safe inference.

The remaining HTTPX/Starlette messages were deprecation warnings and did not cause test failures.

---

## 13. Reproducibility

Phase 4 establishes a reproducible local execution environment.

The system can be started through Docker Compose with the application services separated into explicit containers.

MLflow persistence is provided through the Docker volume:

`mlflow-data`

The training workflow records experiment and model metadata in MLflow, while Git provides source-version traceability.

The model registry provides versioned model artifacts and lifecycle metadata.

Together these components establish the foundation for reproducible experimentation and controlled model serving.

---

## 14. Known Limitations and Deferred Scope

The following items are intentionally outside Phase 4:

* GitHub Actions CI/CD.
* Automated monitoring.
* Data drift detection.
* Prediction-error monitoring.
* Automated retraining.
* Automated production promotion without evaluation.
* Cloud deployment.
* Kubernetes.
* Large-scale distributed infrastructure.
* Large LLM or agent infrastructure.

These are deferred to later phases only where they solve an actual lifecycle or engineering problem.

---

## 15. Phase 4 Engineering Decisions

### MLflow is the lifecycle authority

MLflow is used for experiment tracking, model registration, model versioning and lifecycle metadata.

### No forced production model

A learned model is not promoted simply because it is the strongest learned model.

It must first beat the persistence baseline under the defined evaluation criterion.

### Baseline remains operational

When no learned model qualifies for production, the persistence baseline remains available as the serving strategy.

### Docker remains local-first

Docker Compose provides reproducibility without introducing unnecessary cloud infrastructure.

### Model-service image remains focused

The MLflow-serving model service does not bundle the complete dataset or local model directory when operating through the MLflow lifecycle.

---

## 16. Phase 4 Completion Checklist

* [x] Dockerfiles created and integrated.
* [x] Docker Compose configuration operational.
* [x] React web container operational.
* [x] Node/Express API container operational.
* [x] FastAPI model-service container operational.
* [x] MLflow container operational.
* [x] Persistent MLflow Docker volume configured.
* [x] MLflow experiment tracking implemented.
* [x] Model Registry implemented.
* [x] Model versions registered.
* [x] Candidate evaluation implemented.
* [x] Baseline-aware promotion guard implemented.
* [x] Rejected candidate state recorded.
* [x] Baseline fallback serving implemented.
* [x] Health endpoint verified.
* [x] Readiness endpoint verified.
* [x] API health verified.
* [x] MLflow model signatures verified.
* [x] End-to-end prediction verified.
* [x] 20/20 automated tests passing.
* [x] Dockerized runtime verified.
* [x] Phase 4 engineering decisions documented.
* [x] Phase 4 completion report created.
* [x] Phase 4 Git checkpoint committed and pushed.

---

## 17. Git Checkpoint

Phase 4 implementation changes were committed and pushed to the `master` branch.

The final Phase 4 documentation changes are committed separately as the documentation closure checkpoint.

The repository should have a clean working tree after the final documentation commit.

---

## 18. Phase 4 Final State

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
Evaluation + Baseline Guard
  ↓
Production Decision
  ↓
Model Service
  ↓
Node API
  ↓
React Dashboard
```

The system is no longer only a collection of ML experiments and application components.

It now has an explicit model lifecycle with:

* reproducible local infrastructure,
* tracked experiments,
* versioned models,
* evaluation-based promotion,
* safe baseline fallback,
* containerized serving,
* validated model contracts,
* and verified end-to-end inference.

---

## 19. Phase 5 Entry Point

Phase 4 establishes the infrastructure required for the next lifecycle layer.

Phase 5 will focus on:

```text
Quality Gates
    ↓
Continuous Testing
    ↓
CI
    ↓
Monitoring
    ↓
Drift Detection
    ↓
Performance Detection
    ↓
Controlled Retraining
# PHASE 4 — COMPLETE
