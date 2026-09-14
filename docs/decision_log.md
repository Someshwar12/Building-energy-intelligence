# Decision Log

This document records important engineering and architectural decisions made during development of the Building & Energy Intelligence Platform.

The purpose is to preserve the reasoning behind major choices so that future changes can be evaluated against the original design constraints.

---

## Decision 001 — Use BDG2 as the Initial Dataset

**Status:** Accepted

### Decision

Use the Building Data Genome Project 2 (BDG2) dataset as the initial source of building energy and contextual data.

### Reason

BDG2 provides:

- building metadata
- electricity consumption
- weather data
- hourly observations
- multiple buildings

This makes it suitable for developing an end-to-end building-energy intelligence system rather than a simple single-table ML exercise.

---

## Decision 002 — Build the Project Incrementally

**Status:** Accepted

### Decision

Develop the platform through explicit phases instead of implementing the complete stack at once.

### Reason

The project is intended to demonstrate engineering maturity as well as machine-learning ability.

A phased architecture allows each layer to be:

- implemented
- tested
- validated
- documented
- committed to Git

before additional complexity is introduced.

Current progression:

```text
Phase 0
Project Foundation
      ↓
Phase 1
Data + Features + ML Baseline
      ↓
Phase 2
ML Inference Service
      ↓
Phase 3
Application Platform
      ↓
Phase 4
MLOps + Model Lifecycle
````

---
## Decision 003 — Keep the System CPU-First

**Status:** Accepted

### Decision

The initial platform must run locally on a normal development laptop without requiring a GPU.

### Reason

The project is intended to remain:

* accessible
* inexpensive
* reproducible
* easy to develop locally

The initial ML workload does not require GPU infrastructure.

GPU-dependent technologies will therefore not be introduced unless a future requirement genuinely justifies them.

---

## Decision 004 — Do Not Introduce LLMs or Agents

**Status:** Accepted

### Decision

The core platform will not depend on LLMs, autonomous agents, or transformer models.

### Reason

The project is intended to demonstrate conventional ML, data engineering, inference, application architecture, and MLOps skills.

The central problem is building-energy intelligence rather than adding an LLM merely for demonstration purposes.

---

## Decision 005 — Establish a Persistence Baseline

**Status:** Accepted

### Decision

Use persistence forecasting as the primary benchmark baseline.

### Reason

A machine-learning model should not be considered useful simply because it produces predictions.

It must outperform a meaningful baseline.

For short-horizon energy forecasting, persistence provides a simple and interpretable benchmark.

The baseline therefore remains part of model evaluation even after introducing more complex models.

---

## Decision 006 — Retain Random Forest as the Initial ML Challenger

**Status:** Accepted

### Decision

Random Forest is retained as the initial deployable ML challenger even though persistence performed better in the Phase 1 benchmark.

### Reason

The Phase 1 evaluation showed that persistence was the strongest benchmark.

Random Forest was nevertheless retained because it provides a genuine learned model and establishes the initial model-serving path for the platform.

This distinction is important:

```text
Production benchmark champion:
Persistence

Initial learned model:
Random Forest
```

The Random Forest model must not be described as the overall Phase 1 performance champion.

---

## Decision 007 — Preserve Feature Parity Between Training and Inference

**Status:** Accepted

### Decision

The feature construction used by the FastAPI inference service must reproduce the feature definitions established during Phase 1.

### Reason

Training-serving skew can occur when training and inference construct features differently.

The inference service therefore reconstructs the required features from the supplied historical context rather than using an unrelated feature definition.

This establishes a controlled boundary:

```text
Phase 1 Feature Logic
        ↓
Training

Same Feature Contract
        ↓
Inference
```

---

## Decision 008 — Require 168 Hours of Historical Context

**Status:** Accepted

### Decision

The current Random Forest inference contract requires exactly 168 consecutive hourly observations preceding the prediction timestamp.

### Reason

The Phase 1 feature set includes historical and rolling information that requires a sufficient historical window.

Requiring the complete context at the API boundary makes the inference contract explicit and prevents silently producing predictions from incomplete history.

---

## Decision 009 — Separate ML Inference from the Application API

**Status:** Accepted

### Decision

Use a dedicated FastAPI ML service behind a Node.js/Express application API.

The intended request path is:

```text
Next.js
   ↓
Express
   ↓
FastAPI
   ↓
ML Model
```

### Reason

This separation provides clear responsibilities.

The frontend should not need to know:

* how the model is loaded
* how features are constructed
* how the model artifact is serialized
* how inference is performed

The ML service owns those responsibilities.

The Express API acts as the application boundary.

---

## Decision 010 — Use Next.js for the Web Application

**Status:** Accepted

### Decision

Use Next.js with React and TypeScript for the frontend.

### Reason

The application requires:

* structured pages
* reusable components
* typed API interaction
* responsive UI
* interactive analytical visualizations

Next.js provides the application framework while React handles the UI layer.

---

## Decision 011 — Use Express as the Application API

**Status:** Accepted

### Decision

Use Node.js with Express as the application-facing API.

### Reason

The application layer needs to coordinate:

* building metadata
* historical consumption
* prediction context
* ML-service communication

Express provides a lightweight service boundary without introducing unnecessary infrastructure at the current stage.

---

## Decision 012 — Keep API, Service, and Repository Responsibilities Separate

**Status:** Accepted

### Decision

The Express application separates:

```text
Routes
  ↓
Services
  ↓
Repositories
```

### Reason

This prevents route handlers from becoming responsible for data access and business/application logic simultaneously.

For example:

```text
Route
 ↓
Prediction Service
 ↓
Prediction Repository
 ↓
FastAPI
```

This structure also makes future testing and replacement of individual components easier.

---

## Decision 013 — Use Parquet for the Current Processed Dataset

**Status:** Accepted

### Decision

Use:

```text
data/processed/phase1_features.parquet
```

as the canonical Phase 1 processed feature dataset.

### Reason

Parquet provides:

* columnar storage
* efficient analytical access
* a compact representation
* compatibility with Python data workflows

It also keeps the early system simple without requiring a database before one is necessary.

---

## Decision 014 — Do Not Introduce MongoDB in Phase 3

**Status:** Accepted

### Decision

Do not introduce MongoDB or another application database during Phase 3.

### Reason

The current application primarily needs access to a relatively small, static set of building metadata and historical development data.

Introducing a database at this stage would add infrastructure without solving an immediate architectural requirement.

A persistent application database can be introduced later if the platform requires:

* user-specific state
* operational records
* prediction history
* configuration
* alerts
* monitoring records

---

## Decision 015 — Export Building Metadata for the Application Layer

**Status:** Accepted

### Decision

Create an application-facing building metadata file:

```text
apps/api/src/data/buildings.json
```

### Reason

The application currently needs a stable and simple source for building metadata.

This avoids forcing the application API to perform unnecessary data-processing operations every time the building list is requested.

The export is generated from the selected Phase 1 building metadata.

---

## Decision 016 — Keep Historical Consumption Access Separate from Building Metadata

**Status:** Accepted

### Decision

Building metadata and historical consumption are accessed through separate repositories.

### Reason

They have different access patterns and responsibilities.

```text
Building Metadata
      ↓
Building Repository

Historical Consumption
      ↓
Consumption Repository
```

This separation also leaves room for future storage technologies without requiring changes to the frontend contract.

---

## Decision 017 — Use Typed API Contracts

**Status:** Accepted

### Decision

Use TypeScript types for application API responses and Pydantic schemas for FastAPI request/response validation.

### Reason

The system crosses multiple service boundaries.

Explicit contracts reduce ambiguity and make incompatible changes easier to detect.

The current conceptual contract is:

```text
React / TypeScript
        ↓
Express API
        ↓
FastAPI / Pydantic
        ↓
ML Model
```

---

## Decision 018 — Validate the ML Service at Its Boundary

**Status:** Accepted

### Decision

The FastAPI service validates incoming prediction requests before inference.

### Reason

Invalid prediction context should be rejected before it reaches the model.

Validation includes requirements such as:

* valid timestamps
* non-negative energy values
* sufficient historical context
* duplicate detection
* chronological ordering

This turns assumptions in the model pipeline into explicit API constraints.

---

## Decision 019 — Load the Model at Service Startup

**Status:** Accepted

### Decision

The FastAPI ML service loads the model artifact during application startup.

### Reason

Loading the model for every request would introduce unnecessary overhead.

Startup loading also provides an explicit readiness state.

The service exposes:

```text
/health
/ready
```

so that basic service health and model readiness can be distinguished.

---

## Decision 020 — Keep Model Version Information in the Prediction Response

**Status:** Accepted

### Decision

Prediction responses include:

```text
model_name
model_version
```

### Reason

Predictions should be traceable to the model that produced them.

This becomes increasingly important once the platform introduces:

* model versioning
* model promotion
* experiment tracking
* monitoring
* retraining

The current model reports the Phase 1 version.

---

## Decision 021 — Treat the Current Forecast as a Demonstration of Inference

**Status:** Accepted

### Decision

The current application demonstrates model inference using historical BDG2 timestamps.

### Reason

The available dataset ends in 2017.

Therefore, the current forecast endpoint demonstrates the complete prediction pipeline but does not represent a live production forecast of an actual current building.

This distinction must be preserved in future documentation and UI wording.

The system should not claim that the current historical prediction is a live future-energy forecast.

---

## Decision 022 — Keep Phase 3 Focused on Application Integration

**Status:** Accepted

### Decision

Phase 3 focuses on connecting:

```text
ML
+
API
+
Web Application
```

without introducing the complete MLOps stack.

### Reason

The project needs a working end-to-end application before adding lifecycle infrastructure.

Therefore Phase 3 intentionally excludes:

* MLflow
* model registry
* automated model promotion
* drift detection
* production monitoring
* automated retraining
* CI/CD deployment
* cloud deployment
* Docker-based production orchestration

These belong to later phases.

---

## Decision 023 — Introduce MLOps After the End-to-End Application Works

**Status:** Accepted

### Decision

MLOps infrastructure will be introduced after the core application workflow is operational.

### Reason

The platform should first establish:

```text
Data
 ↓
Model
 ↓
Inference
 ↓
API
 ↓
UI
```

before introducing lifecycle automation.

This makes it possible to attach experiment tracking, model management, monitoring, and retraining to a functioning system rather than building infrastructure around an incomplete application.

---

## Decision 024 — Use Champion / Challenger Model Lifecycle

**Status:** Planned

### Decision

Future model lifecycle management will distinguish between a production champion and candidate challengers.

The intended lifecycle is:

```text
Candidate
   ↓
Evaluation
   ↓
Challenger
   ↓
Promotion Gate
   ↓
Champion
```

### Reason

The Phase 1 results already demonstrated why this distinction matters.

A newer or more complex model should not automatically replace an existing model.

Promotion should depend on predefined evaluation criteria.

---

## Decision 025 — Add Experiment Tracking Before Automated Retraining

**Status:** Planned

### Decision

Experiment tracking and model version management should be established before automated retraining is introduced.

### Reason

Automated retraining without traceability makes it difficult to determine:

* which data produced a model
* which parameters were used
* which evaluation results were obtained
* why a model was promoted

The lifecycle should therefore preserve experiment and model lineage before automation is added.

---

## Decision 026 — Monitoring Will Cover Both Data and Model Performance

**Status:** Planned

### Decision

Future monitoring will consider both input-data behavior and model performance.

The planned architecture includes:

```text
Input Data
   ↓
Data Monitoring
   ↓
Prediction
   ↓
Performance Monitoring
```

Potential monitoring areas include:

* feature distribution changes
* missing-data rates
* prediction distributions
* forecast errors
* data drift
* model degradation

### Reason

A model can remain technically available while becoming less useful because the underlying data distribution or model performance changes.

---

## Decision 027 — Retraining Must Be Controlled

**Status:** Planned

### Decision

Future retraining will not automatically promote every newly trained model.

The intended process is:

```text
Monitoring
   ↓
Retraining Trigger
   ↓
Candidate Training
   ↓
Evaluation
   ↓
Promotion Gate
   ↓
Champion
```

### Reason

Automated training and automated deployment are separate decisions.

A candidate model must demonstrate that it is suitable before replacing the current champion.

---

# Current Architecture Decision Summary

The decisions made through Phase 3 establish the following architecture:

```text
                 ┌──────────────────────┐
                 │      Next.js         │
                 │       React          │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │      Express         │
                 │   Application API    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │       FastAPI        │
                 │    ML Inference      │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │   Random Forest      │
                 │    Phase 1 Model     │
                 └──────────────────────┘
```

The architecture is intentionally simple at this stage.

Its purpose is to provide a stable foundation for the next engineering layer:

```text
Experiment Tracking
        ↓
Model Registry
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

Future infrastructure must preserve the existing service boundaries unless there is a clear engineering reason to change them.