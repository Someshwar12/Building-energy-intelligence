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
Data + Features + ML Foundation
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

The project is intended to demonstrate:

* conventional ML
* data engineering
* inference
* application architecture
* MLOps

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

## Decision 006 — Retain Random Forest as the Initial Learned Challenger

**Status:** Accepted

### Decision

Random Forest is retained as the initial learned ML challenger even though persistence performed better in the Phase 1 benchmark.

### Reason

The Phase 1 evaluation showed that persistence was the strongest benchmark.

Random Forest was nevertheless retained because it provides a genuine learned model and establishes the initial model-serving path for the platform.

This distinction is important:

```text
Benchmark Baseline:
Persistence

Initial Learned Model:
Random Forest
```

Random Forest must not be described as the overall Phase 1 performance champion.

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

The forecasting inference contract requires 168 hourly historical observations preceding the prediction timestamp.

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
ML Serving Layer
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
* anomaly analysis
* ML lifecycle information

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

This prevents route handlers from becoming responsible for data access and application logic simultaneously.

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
* compact representation
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
ML Serving
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

## Decision 019 — Load the Serving Configuration at Service Startup

**Status:** Accepted

### Decision

The FastAPI ML service initializes its serving configuration during application startup.

### Reason

Loading and configuring the serving path for every request would introduce unnecessary overhead.

Startup initialization also provides an explicit readiness state.

The service exposes:

```text
/health
/ready
```

so that basic service health and serving readiness can be distinguished.

The serving layer can resolve either:

```text
MLflow-managed learned model
```

or:

```text
Persistence baseline
```

depending on the current lifecycle state.

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

Predictions should be traceable to the serving strategy and model version that produced them.

This becomes increasingly important once the platform introduces:

* model versioning
* model promotion
* experiment tracking
* monitoring
* retraining

The current baseline-serving state reports:

```text
model_name = persistence
model_version = baseline
```

when no learned model owns the production alias.

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

**Status:** Implemented as lifecycle concept

### Decision

The model lifecycle distinguishes between:

* evaluated learned candidates
* a production model when one qualifies
* the persistence baseline when no learned model qualifies

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
Production Model
```

### Reason

The Phase 1 results demonstrated why this distinction matters.

A newer or more complex model should not automatically replace an existing serving strategy.

Promotion should depend on predefined evaluation criteria.

Phase 4 implemented the registry, candidate evaluation, and promotion-gate infrastructure required for this lifecycle.

---

## Decision 025 — Use MLflow as the Lifecycle Authority

**Status:** Accepted

### Decision

MLflow is the lifecycle authority for:

* experiment tracking
* registered model versions
* model artifacts
* lifecycle metadata
* model signatures

### Reason

Model lifecycle state should not depend solely on local `.joblib` files.

MLflow provides a central local registry for the Dockerized system while preserving model lineage and version information.

Local model files remain useful for development and historical artifacts, but the Dockerized lifecycle path uses MLflow.

---

## Decision 026 — Record Reproducibility Metadata

**Status:** Accepted

### Decision

Training runs should record sufficient metadata to make experiments traceable.

Tracked information includes:

* parameters
* validation metrics
* test metrics
* dataset/reference metadata
* configuration
* Git commit information
* model artifacts
* model signatures

### Reason

A model should be traceable to the experiment and source state that produced it.

This establishes the foundation required for reliable model comparison and future retraining.

---

## Decision 027 — Compare Learned Models Against a Common Baseline

**Status:** Accepted

### Decision

The persistence baseline remains part of the model evaluation and promotion process.

### Reason

A learned model should not be promoted merely because it performs better than other learned models.

The system must determine whether the learned candidate provides sufficient improvement over a simple operational benchmark.

The comparison must use the same evaluation criterion on both sides.

---

## Decision 028 — Use a Baseline-Aware Promotion Guard

**Status:** Accepted

### Decision

The promotion system must compare the best evaluated learned model against the persistence baseline using the same promotion metric.

The current promotion metric is:

```text
validation_macro_building_nmae
```

The intended decision is:

```text
Best Evaluated Learned Model
            ↓
Validation Macro-Building NMAE
            ↓
Compare with Persistence
            ↓
        Baseline Guard
          /       \
       PASS       FAIL
        ↓           ↓
   Production    Reject
```

### Reason

The system must not compare incompatible metrics.

In particular, a learned model's macro-building NMAE must not be compared against an aggregate baseline NMAE.

This prevents a metric-definition mismatch from causing an invalid promotion decision.

---

## Decision 029 — Do Not Force a Learned Model into Production

**Status:** Accepted

### Decision

A learned model is not promoted simply to populate the production alias.

### Reason

The evaluation process must be allowed to conclude that the baseline is currently preferable.

If no learned candidate beats the persistence baseline under the defined promotion criterion:

```text
No learned production model
        ↓
Persistence remains operational
```

This preserves the integrity of the evaluation process.

---

## Decision 030 — Keep Persistence as an Operational Fallback

**Status:** Accepted

### Decision

When no valid learned production alias exists, the model service serves the persistence baseline.

### Reason

The application should remain operational even when no learned candidate qualifies for production.

The persistence strategy uses the most recent observed energy value as the next-hour prediction.

The current serving state is therefore:

```text
serving_mode = baseline
model_name = persistence
model_version = baseline
```

This is an intentional lifecycle state rather than a deployment error.

---

## Decision 031 — Register Learned Models in MLflow

**Status:** Accepted

### Decision

Learned model artifacts are registered in the MLflow Model Registry under:

```text
building-energy-forecast
```

The current registered versions are:

```text
v1 — Ridge
v2 — Random Forest
v3 — HistGradientBoosting
```

### Reason

Registry versioning provides a persistent representation of evaluated model artifacts and their lifecycle metadata.

This makes model history inspectable without relying only on filenames in the local `models/` directory.

---

## Decision 032 — Record Rejected Candidates Explicitly

**Status:** Accepted

### Decision

A learned model that fails the promotion guard should remain visible in the registry with an explicit rejected lifecycle state rather than being silently deleted.

### Reason

Rejected candidates are useful for understanding:

* which model was evaluated
* why it was evaluated
* which promotion criterion was used
* why it was not promoted

This creates an auditable model lifecycle.

The current registry contains a rejected Random Forest candidate alongside other evaluated learned versions.

---

## Decision 033 — Verify MLflow Model Signatures

**Status:** Accepted

### Decision

Registered model versions must expose compatible MLflow input signatures.

### Reason

Model signatures provide an explicit representation of the model's expected input contract.

The registered versions were verified against the Docker-hosted MLflow server.

The signatures cover the feature categories required by the forecasting pipeline, including:

* building metadata
* weather features
* calendar features
* lag features
* rolling features
* degree-hour features

This provides an additional safeguard against model/inference contract mismatch.

---

## Decision 034 — Keep the Model-Service Image Focused

**Status:** Accepted

### Decision

When operating through the MLflow lifecycle, the model-service image should not bundle the complete local dataset or local model directory.

### Reason

The serving image should contain the inference application and its required dependencies while retrieving lifecycle-managed model artifacts through MLflow.

This keeps the serving image focused on:

```text
Inference Code
+
Dependencies
+
Serving Configuration
```

rather than duplicating the complete development environment.

---

## Decision 035 — Use Docker Compose for Local Reproducibility

**Status:** Accepted

### Decision

Use Docker Compose to run the local application stack.

The current services are:

```text
Web
API
Model Service
MLflow
```

### Reason

Docker Compose provides reproducible service boundaries and networking without introducing unnecessary cloud infrastructure.

The local service communication is:

```text
Browser
   ↓
Web :3000
   ↓
API :4000
   ↓
Model Service :8000
   ↓
MLflow :5000
```

MLflow state is persisted through the Docker volume:

```text
mlflow-data
```

---

## Decision 036 — Keep Infrastructure Local-First

**Status:** Accepted

### Decision

Docker Compose and MLflow are intentionally used as a local reproducibility layer before introducing cloud infrastructure.

### Reason

The project is designed to prove the engineering workflow locally first.

Cloud deployment, Kubernetes, distributed infrastructure, and other operational complexity should be introduced only when the local lifecycle is stable and there is a genuine requirement for them.

---

## Decision 037 — Keep Model Lifecycle Separate from the Frontend

**Status:** Accepted

### Decision

The frontend should observe model lifecycle information through the application API rather than directly controlling MLflow.

### Reason

The frontend is a presentation layer.

The model lifecycle belongs to the ML/service layer.

The intended boundary is:

```text
Model Lifecycle
      ↓
FastAPI
      ↓
Express API
      ↓
Model Lab UI
```

This prevents the frontend from becoming coupled to MLflow implementation details.

---

## Decision 038 — Introduce Model Lab as an Observability Surface

**Status:** Accepted

### Decision

Provide a dedicated Model Lab interface for inspecting model lifecycle information.

The Model Lab surface exposes information such as:

* registered versions
* model families
* evaluation status
* rejection status
* run information
* metrics
* parameters
* baseline information
* production/serving state

### Reason

The project should make the model lifecycle visible rather than treating MLflow as hidden infrastructure.

Model Lab is an observability surface.

It is not itself the authority that decides model promotion.

---

## Decision 039 — Keep Anomaly Detection Separate from Forecasting

**Status:** Accepted

### Decision

Anomaly detection is implemented as a separate application capability rather than modifying the forecasting model.

### Reason

Forecasting and anomaly detection answer different questions:

```text
Forecasting
"What energy use should occur next?"

Anomaly Detection
"Does this observed energy use look unusual?"
```

Separating the two allows each capability to evolve independently.

The current anomaly service uses historical consumption behavior and a rolling statistical detection approach.

---

## Decision 040 — Keep the Application Database-Free for the Current Scope

**Status:** Accepted

### Decision

Do not introduce an application database merely to support the current dashboard and lifecycle views.

### Reason

The current system can operate using:

* processed Parquet data
* application metadata
* MLflow storage
* model artifacts

A database can be introduced later if the application develops a genuine requirement for persistent operational state.

---

## Decision 041 — Validate the Complete System at Phase Boundaries

**Status:** Accepted

### Decision

Each phase should finish with implementation verification and documentation before the next major phase begins.

### Reason

The project is intended to demonstrate a reproducible engineering process rather than simply a final collection of code.

The expected workflow is:

```text
Implement
   ↓
Run
   ↓
Inspect
   ↓
Verify
   ↓
Document
   ↓
Git Checkpoint
   ↓
Next Phase
```

---

## Decision 042 — Phase 4 Stops at Controlled Model Serving

**Status:** Accepted

### Decision

Phase 4 ends after establishing:

```text
Training
   ↓
Experiment Tracking
   ↓
Model Registry
   ↓
Evaluation
   ↓
Baseline Guard
   ↓
Controlled Serving
```

### Reason

Phase 4 establishes the model lifecycle foundation without prematurely implementing every future MLOps capability.

The following are intentionally deferred:

* GitHub Actions CI/CD
* automated monitoring
* data drift detection
* prediction-performance monitoring
* automated retraining
* automated production promotion without evaluation
* cloud deployment
* Kubernetes
* distributed infrastructure
* large-scale LLM or agent infrastructure

These should be introduced only when their corresponding lifecycle requirements are reached.

---

# Current Architecture Decision Summary

The decisions made through Phase 4 establish the following architecture:

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
                    ┌──────────┴───────────┐
                    │                      │
                    ▼                      ▼
             Persistence             MLflow
              Baseline                 │
                                       ▼
                                Model Registry
                                       │
                                       ▼
                                Evaluation Gate
                                       │
                                       ▼
                                Promotion Decision
```

The architecture is intentionally simple enough to run locally while providing explicit boundaries for future MLOps capabilities.

---

# Phase 4 Final Decision State

Phase 4 established the following decisions as the current operating state:

```text
MLflow
  ↓
Lifecycle Authority

Persistence
  ↓
Benchmark Baseline

Learned Models
  ↓
Evaluated Challengers

Baseline Guard
  ↓
Required for Promotion

No Qualifying Learned Model
  ↓
Persistence Serving

Docker Compose
  ↓
Local Reproducibility

Model Lab
  ↓
Lifecycle Observability
```

The current system therefore does not force a learned model into production.

The persistence baseline remains operational when no learned candidate satisfies the promotion criterion.

This is a deliberate lifecycle decision.

---

# Future Decisions — Planned

## Decision 043 — Add Continuous Quality Gates

**Status:** Planned

Future phases should introduce automated quality gates for:

* tests
* linting
* type checking
* data validation
* model validation
* build verification

The purpose is to prevent known regressions from entering the main branch or deployment pipeline.

---

## Decision 044 — Introduce CI After Local Validation Is Stable

**Status:** Planned

GitHub Actions should be introduced after the local test and build workflow is stable.

The intended flow is:

```text
Git Push
   ↓
CI
   ↓
Tests
   ↓
Lint / Type Checks
   ↓
Build
   ↓
Quality Gate
```

CI should automate verification rather than replace local development.

---

## Decision 045 — Monitor Both Data and Model Performance

**Status:** Planned

Future monitoring will consider both input-data behavior and model performance.

The planned architecture is:

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
* service health

### Reason

A model can remain technically available while becoming less useful because the underlying data distribution or model performance changes.

---

## Decision 046 — Retraining Must Be Controlled

**Status:** Planned

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
Baseline / Production Gate
   ↓
Promotion Decision
   ↓
Serving
```

### Reason

Automated training and automated deployment are separate decisions.

A newly trained candidate must demonstrate that it is suitable before replacing the current serving strategy.

---

## Decision 047 — Preserve Existing Service Boundaries During Future Expansion

**Status:** Planned

Future infrastructure should preserve the current boundaries unless there is a clear engineering reason to change them.

The current boundaries are:

```text
Next.js
   ↓
Express
   ↓
FastAPI
   ↓
MLflow / Model Serving
```

### Reason

The current separation provides a stable foundation for:

* CI
* monitoring
* drift detection
* retraining
* deployment

Future additions should extend these boundaries rather than introduce unnecessary architectural rewrites.

---

# Final Engineering Principle

The project follows one overarching rule:

```text
Do not add infrastructure because it sounds impressive.

Add infrastructure when the system has a real engineering requirement for it.
```

The platform should therefore evolve from:

```text
Data
 ↓
ML
 ↓
Inference
 ↓
Application
 ↓
Lifecycle
 ↓
Quality
 ↓
Monitoring
 ↓
Retraining
 ↓
Deployment
```

with each layer introduced only after the previous layer is sufficiently validated.