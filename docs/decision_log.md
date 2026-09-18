I’ve converted the existing decision history into a **final, project-complete 
# Decision Log

This document records the final engineering and architectural decisions made during development of the Building & Energy Intelligence Platform.

The purpose of this document is to preserve the reasoning behind major technical choices and to provide an auditable record of the architecture, ML lifecycle, monitoring design, and final model lifecycle outcome.

The project is complete at Phase 6. There is no subsequent implementation phase.

---

# 1. Project and Data Foundations

## Decision 001 — Use BDG2 as the Initial Dataset

**Status:** Final

### Decision

Use the Building Data Genome Project 2 (BDG2) dataset as the source of building energy, metadata, and weather information.

### Reason

BDG2 provides:

- building metadata
- electricity consumption
- weather data
- hourly observations
- multiple buildings

This makes it suitable for demonstrating an end-to-end building-energy intelligence platform rather than a single-table ML exercise.

---

## Decision 002 — Develop the Platform Incrementally

**Status:** Final

### Decision

Develop the platform through explicit implementation phases, validating and documenting each major architectural layer before introducing the next layer.

### Reason

The project is intended to demonstrate engineering maturity in addition to machine-learning ability.

The completed development progression was:

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
      ↓
Phase 5
Testing + CI + Observability
      ↓
Phase 6
Controlled Retraining + Final Lifecycle
````

Phase 6 is the final implementation phase.

There is no Phase 7.

---

## Decision 003 — Keep the System CPU-First

**Status:** Final

### Decision

The platform must run locally on a normal development laptop without requiring a GPU.

### Reason

The project is intended to remain:

* accessible
* inexpensive
* reproducible
* locally runnable
* practical to demonstrate

The current workload does not justify GPU infrastructure.

---

## Decision 004 — Do Not Introduce LLMs or Autonomous Agents

**Status:** Final

### Decision

The core platform does not depend on:

* LLMs
* autonomous agents
* transformer models
* LLM serving infrastructure

### Reason

The project demonstrates:

* conventional machine learning
* data engineering
* inference
* application architecture
* MLOps
* monitoring
* controlled model lifecycle management

LLMs or agents would not provide necessary functionality for the core building-energy problem.

---

## Decision 005 — Establish Persistence as the Primary Baseline

**Status:** Final

### Decision

Use persistence forecasting as the primary benchmark and operational reference.

### Reason

A learned model should not be considered useful merely because it generates predictions.

It must demonstrate value relative to a meaningful baseline.

The persistence strategy is:

```text
Latest observed energy value
        ↓
Next-hour prediction
```

Persistence therefore remains part of:

* model evaluation
* promotion
* serving
* performance monitoring
* retraining eligibility
* candidate evaluation

---

## Decision 006 — Retain Learned Models as Evaluated Challengers

**Status:** Final

### Decision

Retain learned models in MLflow even when persistence performs better.

The learned model families are:

```text
Ridge
Random Forest
HistGradientBoosting
```

### Reason

The project must demonstrate a real ML lifecycle.

A learned model can be:

```text
trained
→ registered
→ evaluated
→ compared
→ rejected
```

without being incorrectly represented as a production model.

---

# 2. ML and Inference Architecture

## Decision 007 — Preserve Feature Parity Between Training and Inference

**Status:** Final

### Decision

Inference must reproduce the feature definitions established during model development.

### Reason

Training-serving skew can occur when training and inference construct features differently.

The architecture therefore maintains:

```text
Feature Definition
       ↓
Training
       ↓
Registered Model

Same Feature Definition
       ↓
Inference
```

---

## Decision 008 — Require 168 Hours of Historical Context

**Status:** Final

### Decision

The prediction contract requires 168 hourly historical observations preceding the prediction timestamp.

### Reason

The forecasting feature set requires sufficient historical context for:

* lag features
* rolling statistics
* temporal features
* historical energy behavior

The requirement is validated at the FastAPI boundary.

---

## Decision 009 — Separate ML Inference from the Application API

**Status:** Final

### Decision

Use a dedicated FastAPI ML service behind the Node.js/Express application API.

### Architecture

```text
Next.js
   ↓
Express
   ↓
FastAPI
   ↓
ML Serving Strategy
```

### Reason

The frontend and application layer should not need to know:

* how the model is loaded
* how features are constructed
* how artifacts are serialized
* how inference is performed

The ML service owns those responsibilities.

---

## Decision 010 — Use Next.js for the Web Application

**Status:** Final

### Decision

Use Next.js with React and TypeScript for the frontend.

### Reason

The application requires:

* structured pages
* reusable components
* typed API interaction
* responsive UI
* analytical visualization

---

## Decision 011 — Use Express as the Application API

**Status:** Final

### Decision

Use Node.js with Express as the application-facing API.

### Reason

The application layer coordinates:

* building metadata
* historical consumption
* prediction context
* ML-service communication
* anomaly analysis
* Model Lab information
* monitoring information

Express provides a lightweight application boundary appropriate for the current system.

---

## Decision 012 — Separate Routes, Services, and Repositories

**Status:** Final

### Decision

The Express application uses:

```text
Routes
  ↓
Services
  ↓
Repositories
```

### Reason

This prevents route handlers from simultaneously owning:

* HTTP handling
* business logic
* data access

It also makes individual layers easier to test and replace.

---

## Decision 013 — Use Parquet for the Canonical Processed Dataset

**Status:** Final

### Decision

Use:

```text
data/processed/phase1_features.parquet
```

as the canonical processed feature dataset.

### Reason

Parquet provides:

* columnar storage
* efficient analytical access
* compact representation
* compatibility with Python data workflows

A database is not required for the current historical dataset.

---

## Decision 014 — Do Not Introduce an Application Database

**Status:** Final

### Decision

Do not introduce MongoDB or another dedicated application database for the completed scope.

### Reason

The current system can operate using:

* processed Parquet data
* application metadata
* MLflow storage
* model artifacts
* bounded in-memory monitoring state

A database would add infrastructure without being required by the completed product.

---

## Decision 015 — Export Building Metadata for the Application

**Status:** Final

### Decision

Use:

```text
apps/api/src/data/buildings.json
```

as the application-facing building metadata source.

### Reason

The application needs a stable, simple building metadata interface.

This avoids unnecessary data-processing work on every building request.

---

## Decision 016 — Separate Building Metadata from Historical Consumption

**Status:** Final

### Decision

Building metadata and historical consumption use separate repositories.

### Architecture

```text
Building Metadata
      ↓
Building Repository

Historical Consumption
      ↓
Consumption Repository
```

### Reason

The two datasets have different purposes and access patterns.

---

## Decision 017 — Use Explicit API Contracts

**Status:** Final

### Decision

Use:

* TypeScript types for application API contracts
* Pydantic schemas for FastAPI request/response validation

### Reason

The platform crosses multiple service boundaries.

Explicit contracts make incompatible changes easier to detect.

---

## Decision 018 — Validate Prediction Requests at the ML Boundary

**Status:** Final

### Decision

FastAPI validates prediction requests before inference.

Validation includes conditions such as:

* valid timestamps
* non-negative energy values
* sufficient historical context
* unique observations
* chronological ordering
* valid request structure

### Reason

Invalid prediction context should fail explicitly before reaching the model.

---

## Decision 019 — Initialize Serving Configuration at Startup

**Status:** Final

### Decision

The FastAPI service initializes its serving configuration during startup.

### Reason

This avoids repeatedly resolving model configuration for every request and provides explicit readiness information.

The service exposes:

```text
/health
/ready
```

---

## Decision 020 — Include Model Identity in Prediction Responses

**Status:** Final

### Decision

Prediction responses expose:

```text
model_name
model_version
```

and the serving state identifies whether the system is using a learned model or the persistence baseline.

### Reason

Predictions must be traceable to the serving strategy that produced them.

The final baseline-serving state is:

```text
model_name = persistence
model_version = baseline
serving_mode = baseline
```

---

## Decision 021 — Treat the Current Forecast as a Historical Inference Demonstration

**Status:** Final

### Decision

The current forecasting application is a historical-data inference demonstration, not a live telemetry forecasting platform.

### Reason

The BDG2 development data ends in 2017.

Therefore the project must not describe its current historical inference as live real-world building telemetry.

The distinction is:

```text
Current System
Historical inference demonstration

Not implemented
Live operational telemetry
```

---

# 3. Application Architecture

## Decision 022 — Keep Application Integration Separate from MLOps Infrastructure

**Status:** Final

### Decision

The application layer and ML lifecycle infrastructure remain separate concerns.

### Reason

The application must first provide a stable:

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

path.

ML lifecycle infrastructure operates around that path rather than replacing it.

---

## Decision 023 — Introduce MLOps Around a Working Application

**Status:** Final

### Decision

MLOps infrastructure is attached to the functioning application and inference system.

### Reason

This ensures that:

* experiment tracking
* model management
* monitoring
* retraining
* promotion
* rollback

operate around a real application rather than an isolated notebook.

---

## Decision 024 — Use a Champion/Challenger Lifecycle

**Status:** Final

### Decision

The model lifecycle distinguishes between:

* persistence baseline
* evaluated learned candidates
* learned production model when one qualifies

### Architecture

```text
Candidate
   ↓
Evaluation
   ↓
Promotion Gate
   ↓
Production
```

A learned candidate does not become production merely because it is newer or better than other learned candidates.

---

## Decision 025 — Use MLflow as the Lifecycle Authority

**Status:** Final

### Decision

MLflow is the lifecycle authority for:

* experiments
* model runs
* model artifacts
* registered versions
* model signatures
* lifecycle metadata
* aliases

### Reason

Model lifecycle state should not depend only on local `.joblib` files.

MLflow provides the registry and lineage required by the completed architecture.

---

## Decision 026 — Record Reproducibility Metadata

**Status:** Final

### Decision

Training runs record sufficient metadata to trace model creation.

Tracked information includes:

* parameters
* validation metrics
* test metrics
* dataset/reference metadata
* configuration
* Git information
* artifacts
* model signatures
* model-family information
* lifecycle metadata where applicable

### Reason

A model should be traceable to the experiment and source state that produced it.

---

## Decision 027 — Compare Learned Models Against a Common Baseline

**Status:** Final

### Decision

Learned models must be evaluated against persistence using the same relevant evaluation definition.

### Reason

Being better than another learned model is not sufficient evidence that a learned model should replace the operational baseline.

---

## Decision 028 — Use a Baseline-Aware Promotion Guard

**Status:** Final

### Decision

Promotion requires comparison of the candidate learned model against persistence using the defined promotion metric.

The promotion metric is:

```text
validation_macro_building_nmae
```

### Reason

The system must not compare incompatible metrics.

The promotion guard therefore preserves metric-definition consistency.

---

## Decision 029 — Never Force a Learned Model into Production

**Status:** Final

### Decision

A learned model is not promoted merely to populate the production alias.

### Reason

The lifecycle must be able to conclude:

```text
No learned candidate qualifies
        ↓
Persistence remains operational
```

This is a valid lifecycle outcome.

---

## Decision 030 — Use Persistence as the Operational Fallback

**Status:** Final

### Decision

When no valid learned model owns the production alias, FastAPI serves persistence.

### Final serving state

```text
serving_mode = baseline
model_name = persistence
model_version = baseline
```

### Reason

The application remains operational without bypassing the model-promotion gate.

---

## Decision 031 — Register Learned Models in MLflow

**Status:** Final

### Decision

Learned models are registered under:

```text
building-energy-forecast
```

The initial learned versions are:

```text
v1 — Ridge
v2 — Random Forest
v3 — HistGradientBoosting
```

Phase 6 candidate versions are:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

---

## Decision 032 — Preserve Rejected Candidates

**Status:** Final

### Decision

Rejected models remain represented in MLflow with lifecycle metadata rather than being silently deleted.

### Reason

A rejected candidate provides valuable lifecycle evidence:

* what was trained
* what was evaluated
* which metrics were used
* why it was rejected

This creates an auditable model history.

---

## Decision 033 — Verify MLflow Model Signatures

**Status:** Final

### Decision

Registered model versions must preserve compatible MLflow input signatures.

### Reason

Model signatures provide an explicit representation of the model input contract.

The registered model versions were verified against the Docker-hosted MLflow server.

---

## Decision 034 — Keep the Model-Service Image Focused

**Status:** Final

### Decision

The model-service container focuses on:

* inference code
* required dependencies
* serving configuration
* MLflow model access
* monitoring

rather than bundling the complete development dataset and model-development environment.

---

## Decision 035 — Use Docker Compose for Local Reproducibility

**Status:** Final

### Decision

Use Docker Compose for the local production-style stack.

Services:

```text
Web
API
Model Service
MLflow
```

### Reason

Docker Compose provides:

* reproducible service boundaries
* local networking
* isolated dependencies
* persistent MLflow storage

without requiring cloud infrastructure.

---

## Decision 036 — Keep Infrastructure Local-First

**Status:** Final

### Decision

The completed project remains local-first.

Cloud infrastructure, Kubernetes, distributed systems, and similar infrastructure are not required by the current scope.

### Reason

The project prioritizes:

```text
Correctness
+
Reproducibility
+
Testability
+
Observability
+
Clear Architecture
```

over infrastructure complexity that does not solve a current requirement.

---

## Decision 037 — Keep Model Lifecycle Separate from the Frontend

**Status:** Final

### Decision

The frontend does not directly control MLflow.

The boundary is:

```text
ML Lifecycle
      ↓
FastAPI
      ↓
Express API
      ↓
Model Lab
```

### Reason

The frontend is a presentation and interaction layer, not the lifecycle authority.

---

## Decision 038 — Use Model Lab as a Lifecycle Observability Surface

**Status:** Final

### Decision

Model Lab exposes:

* registered versions
* model families
* runs
* metrics
* parameters
* baseline information
* evaluation state
* lifecycle state
* production/serving state

### Reason

The ML lifecycle should be visible as part of the product.

Model Lab does not independently decide production state.

---

## Decision 039 — Keep Anomaly Detection Separate from Forecasting

**Status:** Final

### Decision

Anomaly detection is a separate application capability.

### Reason

Forecasting and anomaly detection answer different questions:

```text
Forecasting
"What should happen next?"

Anomaly Detection
"Does this observed behavior look unusual?"
```

The anomaly service therefore does not modify the forecasting model.

---

## Decision 040 — Keep the Application Database-Free

**Status:** Final

### Decision

The completed application does not require a dedicated application database.

### Reason

The current architecture is adequately represented by:

```text
Processed Data
+
Application Metadata
+
MLflow
+
Model Artifacts
+
Bounded Monitoring State
```

---

# 4. Engineering Verification Decisions

## Decision 041 — Validate the System at Major Boundaries

**Status:** Final

### Decision

Major architectural changes must be verified through explicit testing and build checks.

The working pattern is:

```text
Implement
   ↓
Run
   ↓
Verify
   ↓
Document
   ↓
Git Checkpoint
```

---

## Decision 042 — Complete Phase 4 at Controlled Model Serving

**Status:** Final

### Decision

Phase 4 established:

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

This became the foundation for monitoring and retraining.

---

# 5. Testing and CI Decisions

## Decision 043 — Treat Testing as a Multi-Layer Concern

**Status:** Final

### Decision

Testing covers multiple layers rather than only isolated functions.

The completed testing architecture covers:

```text
Unit
 ↓
Integration
 ↓
Service / API Contracts
 ↓
Application Verification
 ↓
Build Verification
```

---

## Decision 044 — Test Data Validation Explicitly

**Status:** Final

### Decision

Data validation behavior is explicitly tested.

Coverage includes conditions such as:

* required columns
* expected types
* null handling
* invalid energy values
* duplicate timestamps
* timestamp ordering
* frequency
* gaps
* building identity
* weather assumptions
* target alignment

---

## Decision 045 — Test Temporal Feature Correctness

**Status:** Final

### Decision

Temporal feature construction is tested for:

* lag correctness
* rolling-window behavior
* required history
* missing-history behavior
* schema
* temporal leakage prevention

### Reason

Forecasting systems are particularly sensitive to temporal leakage and incorrect alignment.

---

## Decision 046 — Test Model Behavior Separately from Model Quality

**Status:** Final

### Decision

Tests verify structural model behavior without treating successful tests as evidence of predictive superiority.

Examples include:

* prediction exists
* prediction is finite
* prediction is non-negative
* identity is returned
* version is returned
* serving mode is represented
* persistence behavior is correct
* inference contracts remain valid

---

## Decision 047 — Test the Prediction API Boundary

**Status:** Final

### Decision

The prediction API is tested with valid and invalid requests.

The contract covers conditions such as:

* insufficient history
* duplicate observations
* invalid energy values
* invalid timestamps
* malformed payloads
* health
* readiness
* prediction response structure

---

## Decision 048 — Test Application Integration Paths

**Status:** Final

### Decision

The application verifies the major paths connecting:

* buildings
* consumption
* forecasts
* anomalies
* Model Lab
* monitoring

### Reason

The value of the platform comes from the complete system path rather than isolated services.

---

## Decision 049 — Use Automated CI Quality Gates

**Status:** Final

### Decision

Core repository quality checks are automated through GitHub Actions.

The verification categories include:

* Python tests
* Python linting
* API type checking
* API build
* frontend linting
* frontend build
* relevant contracts

---

## Decision 050 — Keep Linting, Type Checking and Builds Separate

**Status:** Final

### Decision

Linting, type checking, and builds are separate verification signals.

```text
Lint
 ↓
Static code-quality verification

Typecheck
 ↓
Type correctness

Build
 ↓
Production artifact verification
```

A successful build does not replace the other checks.

---

## Decision 051 — Keep Normal CI Fast and Deterministic

**Status:** Final

### Decision

Normal CI prioritizes deterministic checks that provide useful feedback without requiring expensive historical processing.

Normal verification includes:

* tests
* lint
* type checking
* contracts
* application builds

---

## Decision 052 — Keep Expensive Validation Outside Normal CI

**Status:** Final

### Decision

The following are not required for every normal commit:

* complete historical retraining
* large-scale model evaluation
* full Docker rebuild
* large data ingestion
* production cloud deployment

This prevents normal development from becoming unnecessarily slow.

---

# 6. Monitoring Decisions

## Decision 053 — Add Operational Prediction Monitoring

**Status:** Final

### Decision

The model service records operational prediction information.

Relevant information includes:

```text
building_id
timestamp
prediction
persistence_baseline
model_name
model_version
serving_mode
```

### Reason

Predictions must be observable after inference.

---

## Decision 054 — Keep Monitoring State Bounded

**Status:** Final

### Decision

The current monitoring implementation uses bounded in-memory state.

### Reason

The project is a local platform and does not require a persistent telemetry database for the completed scope.

Bounded state prevents uncontrolled memory growth.

---

## Decision 055 — Separate Monitoring Events from Historical Dataset Rows

**Status:** Final

### Decision

Operational monitoring observations are not treated as historical training rows.

The conceptual distinction is:

```text
Historical Dataset Row
        ≠
Operational Prediction Observation
```

### Reason

The historical dataset and operational telemetry have different meanings and lifecycles.

---

## Decision 056 — Separate Prediction Observations from Performance Observations

**Status:** Final

### Decision

A prediction observation is created when a prediction is generated.

A performance observation is created only when the actual outcome becomes available.

```text
Prediction
   ↓
Prediction Observation
   ↓
Actual Outcome
   ↓
Performance Observation
```

### Reason

Prediction accuracy cannot be calculated without the corresponding actual value.

---

## Decision 057 — Use Persistence in Performance Monitoring

**Status:** Final

### Decision

Performance monitoring compares the served strategy against persistence when outcomes are available.

### Reason

This maintains baseline awareness throughout the entire ML lifecycle.

---

## Decision 058 — Calculate Global and Per-Building Performance

**Status:** Final

### Decision

Performance monitoring supports both aggregate and building-level analysis.

Metrics include:

* MAE
* RMSE
* NMAE
* persistence MAE
* persistence RMSE
* persistence NMAE

### Reason

Aggregate performance can hide localized degradation.

---

## Decision 059 — Require Sufficient Observations Before Declaring Degradation

**Status:** Final

### Decision

The system does not declare degradation from a small number of observations.

Current configuration:

```text
Recent window size:       30 observations
Sustained windows:         3
Minimum observations:     90
```

Fewer than 90 observations results in:

```text
insufficient_data
```

---

## Decision 060 — Require Sustained Degradation

**Status:** Final

### Decision

A degraded state requires the degradation condition to persist across all required performance windows.

```text
30 observations
      ↓
Window 1

30 observations
      ↓
Window 2

30 observations
      ↓
Window 3

90 observations
      ↓
Sustained Degradation
```

### Reason

A single poor prediction or short-lived performance fluctuation is insufficient evidence for lifecycle action.

---

## Decision 061 — Use a Relative Degradation Threshold

**Status:** Final

### Decision

The current degradation detector uses a 10% relative threshold.

### Reason

Relative performance deterioration is more interpretable across buildings with different energy-consumption scales.

---

## Decision 062 — Use Reference-Based Drift Monitoring

**Status:** Final

### Decision

Current feature distributions are compared against a reference feature profile.

```text
Reference Distribution
        +
Current Distribution
        ↓
Drift Measurement
```

### Reason

Incoming data can differ from the development reference population.

---

## Decision 063 — Use PSI for Current Drift Detection

**Status:** Final

### Decision

Population Stability Index (PSI) is used for the current feature-drift implementation.

Current interpretation:

```text
Healthy:   PSI < 0.10

Warning:   0.10 <= PSI < 0.25

Critical:  PSI >= 0.25
```

---

## Decision 064 — Require Minimum Drift Samples

**Status:** Final

### Decision

At least 30 observations are required before a feature drift evaluation is treated as meaningful.

### Reason

A single observation cannot establish a distribution shift.

---

## Decision 065 — Distinguish Missing Reference Data from No Drift

**Status:** Final

### Decision

The system distinguishes:

```text
Reference Unavailable
```

from:

```text
No Significant Drift
```

### Reason

Missing reference data is not evidence that the current distribution is stable.

---

## Decision 066 — Handle Optional Weather Fields Safely

**Status:** Final

### Decision

Missing optional weather fields must not cause monitoring instrumentation to break a valid prediction request.

### Reason

Monitoring is secondary to the primary prediction path.

The intended order is:

```text
Valid Request
   ↓
Prediction
   ↓
Monitoring
```

---

## Decision 067 — Keep Drift Separate from Retraining

**Status:** Final

### Decision

Drift does not independently trigger retraining.

### Reason

Distribution shift does not necessarily mean predictive performance has become unacceptable.

The lifecycle is:

```text
Drift
 ↓
Supporting Evidence
 ↓
Performance Evaluation
 ↓
Sustained Degradation
 ↓
Retraining Eligibility
```

---

## Decision 068 — Keep Data Quality Separate from Model Degradation

**Status:** Final

### Decision

Poor performance must be interpreted alongside data quality.

### Reason

Invalid or incomplete inputs can produce poor predictions without indicating model degradation.

---

## Decision 069 — Monitor Service Health Separately from Model Quality

**Status:** Final

### Decision

Service health and model quality are separate monitoring dimensions.

Service health includes:

* request behavior
* errors
* latency
* health state
* readiness
* dependency availability

### Reason

A service can be healthy while a model performs poorly, and a model can be healthy while the service is unavailable.

---

## Decision 070 — Do Not Treat Drift as Model Failure by Itself

**Status:** Final

### Decision

Drift alone is not interpreted as model failure.

The system separately tracks:

```text
Data Quality
Drift
Performance
Service Health
```

---

## Decision 071 — Use Explicit Monitoring States

**Status:** Final

### Decision

Monitoring uses explicit states where applicable.

Examples include:

```text
Healthy
Warning
Critical
Insufficient Data
Reference Unavailable
```

### Reason

Explicit states are easier to test, display, aggregate, and consume programmatically.

---

## Decision 072 — Separate Monitoring from Lifecycle Action

**Status:** Final

### Decision

Monitoring produces evidence; lifecycle logic decides whether that evidence is sufficient for retraining.

The architecture is:

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
```

Monitoring does not directly train, promote, or replace models.

---

# 7. Retraining Eligibility Decisions

## Decision 073 — Use an Explicit Retraining Eligibility Contract

**Status:** Final — Implemented

### Decision

Retraining eligibility is evaluated through an explicit structured contract.

The evaluator considers:

* sufficient observations
* sustained performance degradation
* persistence comparison
* drift state
* data-quality state
* service state
* current model identity

The resulting decision includes:

```text
retraining_eligible
status
model
evidence
metrics
reasons
blocking_reasons
```

### Reason

Retraining must be evidence-based rather than triggered by one isolated signal.

---

## Decision 074 — Use State-Based Monitoring-to-Retraining Logic

**Status:** Final — Implemented

### Decision

The completed lifecycle separates:

```text
Normal
 ↓
Monitoring Signals
 ↓
Evidence Accumulation
 ↓
Sustained Degradation
 ↓
Retraining Eligibility
 ↓
Candidate Training
```

### Reason

Transient events should not automatically become retraining events.

---

## Decision 075 — Preserve the Current Serving Strategy Until a Candidate Qualifies

**Status:** Final — Implemented

### Decision

Monitoring and retraining eligibility do not directly replace the serving strategy.

The lifecycle is:

```text
Current Serving Strategy
        ↓
Monitoring
        ↓
Retraining Eligibility
        ↓
Candidate Training
        ↓
Candidate Evaluation
        ↓
Promotion Decision
        ↓
New Production
```

### Reason

Production state must remain stable until a replacement candidate satisfies the required gates.

---

## Decision 076 — Expose Monitoring Through the Application

**Status:** Final — Implemented

### Decision

Monitoring information is exposed through the service/API boundaries and displayed in the Monitoring interface.

### Reason

Operational observability is part of the product rather than hidden only inside logs.

---

## Decision 077 — Keep Monitoring Secondary to the Prediction Path

**Status:** Final

### Decision

Monitoring instrumentation must not unnecessarily break valid inference.

### Reason

Forecast generation is the primary application capability.

Monitoring exists around that capability.

---

# 8. Docker and Runtime Decisions

## Decision 078 — Verify Significant Runtime Changes in Docker

**Status:** Final

### Decision

Runtime-affecting model-service changes must be verified in the Dockerized environment.

### Reason

The local Python environment and Docker environment have different dependency and filesystem boundaries.

---

## Decision 079 — Rebuild Only Required Docker Services

**Status:** Final

### Decision

When a change affects one service, rebuild that service rather than unnecessarily rebuilding the complete stack.

### Reason

The model-service image can be expensive to rebuild.

Model promotion, rejection, and rollback through MLflow do not inherently require a Docker image rebuild because registry state is separate from the container image.

---

## Decision 080 — Treat Dependency Resolution as a Reproducibility Concern

**Status:** Final

### Decision

Dependency-resolution failures are treated separately from application-logic failures.

### Reason

The Docker environment resolves dependencies independently of the local development environment.

Dependency constraints therefore remain part of the reproducibility boundary.

---

## Decision 081 — Preserve Explicit Verification Evidence

**Status:** Final

### Decision

Project completion is supported by explicit test, lint, type-check, and build evidence.

Final verification included:

```text
pytest
Ruff
API typecheck
API build
Web lint
Web build
```

The final Python test suite completed with:

```text
64 passed, 2 warnings
```

Ruff completed successfully.

The API typecheck completed successfully.

The API production build completed successfully.

The frontend lint completed successfully.

The frontend production build completed successfully.

---

## Decision 082 — Keep Monitoring Infrastructure Local and Lightweight

**Status:** Final

### Decision

The monitoring architecture remains local and lightweight.

It does not require:

* Kubernetes
* distributed tracing infrastructure
* external monitoring SaaS
* production-scale telemetry storage
* message queues
* streaming infrastructure

### Reason

The completed platform is designed to demonstrate the MLOps lifecycle on a normal development laptop.

---

# 9. Data and Lifecycle Boundaries

## Decision 083 — Preserve the Historical Development Population

**Status:** Final

### Decision

The selected BDG2 development population remains the reference foundation.

Current scope:

```text
12 buildings
17,544 rows per building
210,528 processed rows
2016-01-01 through 2017-12-31
```

### Reason

A stable reference population is required for:

* feature engineering
* model evaluation
* baseline comparison
* reference distributions
* reproducibility

---

## Decision 084 — Keep Historical Data, Monitoring Data, and MLflow Metadata Separate

**Status:** Final

### Decision

The platform maintains separate conceptual data classes:

```text
Historical Analytical Data
Operational Monitoring Data
Model Lifecycle Metadata
```

### Reason

These classes serve different purposes.

```text
Historical Data
      ↓
Training / Application Context

Monitoring Data
      ↓
Operational Observation

MLflow Metadata
      ↓
Model Lifecycle
```

---

## Decision 085 — Keep Persistence First-Class Across the Entire Lifecycle

**Status:** Final

### Decision

Persistence remains a first-class reference during:

```text
Evaluation
Promotion
Serving
Performance Monitoring
Retraining Eligibility
Candidate Evaluation
```

### Reason

Persistence is not merely a Phase 1 benchmark.

It is the operational reference against which learned-model value is judged throughout the lifecycle.

---

## Decision 086 — Keep Model Lab and Monitoring Separate

**Status:** Final

### Decision

Model Lab and Monitoring remain distinct observability surfaces.

```text
Model Lab
    ↓
Experiments / Registry / Lifecycle

Monitoring
    ↓
Runtime / Predictions / Drift / Performance / Service Health
```

### Reason

Model lifecycle information and runtime behavior are related but distinct concerns.

---

## Decision 087 — Document the Historical-Data Limitation Explicitly

**Status:** Final

### Decision

Documentation must explicitly state that the current system uses historical BDG2 data and does not represent a live building telemetry deployment.

### Reason

The data source ends in 2017.

The project demonstrates the architecture of operational ML rather than claiming access to current live building telemetry.

---

## Decision 088 — Do Not Add Production-Scale Infrastructure Without a Requirement

**Status:** Final

### Decision

The completed architecture does not add infrastructure merely to make the project appear more advanced.

Examples intentionally excluded:

* Kubernetes
* distributed streaming
* distributed databases
* GPU infrastructure
* LLM infrastructure
* unnecessary cloud infrastructure

### Reason

The project prioritizes:

```text
Correctness
+
Reproducibility
+
Clear Architecture
+
Testability
+
Observability
+
Controlled Lifecycle
```

---

# 10. Phase 6 Final Lifecycle Decisions

## Decision 089 — Retraining Begins Only from Explicit Eligibility

**Status:** Final — Implemented

### Decision

Controlled retraining begins from an explicit retraining-eligibility evaluation.

Retraining eligibility requires evidence rather than a single trigger.

The evaluator considers:

```text
Sufficient observations
+
Sustained degradation
+
Baseline comparison
+
Acceptable data quality
+
Operational service state
+
Supporting drift evidence
```

### Reason

Retraining should be a controlled lifecycle action.

---

## Decision 090 — Require Sufficient Observations Before Candidate Training

**Status:** Final — Implemented

### Decision

Candidate retraining requires sufficient performance observations.

### Reason

A candidate trained from too little operational evidence could reflect temporary noise rather than a meaningful change in the underlying system.

---

## Decision 091 — Require Sustained Performance Degradation

**Status:** Final — Implemented

### Decision

Retraining eligibility requires sustained performance degradation rather than a single poor observation.

### Reason

The degradation detector already establishes the required evidence across multiple windows.

Retraining consumes this evidence rather than bypassing it.

---

## Decision 092 — Use Drift as Supporting Evidence

**Status:** Final — Implemented

### Decision

Feature drift can support a retraining decision but cannot independently trigger retraining.

### Reason

Distribution change does not prove predictive degradation.

The lifecycle therefore distinguishes:

```text
Drift
```

from:

```text
Performance Degradation
```

and combines them as contextual evidence.

---

## Decision 093 — Require Baseline-Aware Evaluation After Retraining

**Status:** Final — Implemented

### Decision

Every retrained candidate must be evaluated against persistence before it can qualify for promotion.

### Reason

Retraining cannot bypass the project's original model-quality principle.

The lifecycle is:

```text
Candidate
   ↓
Evaluation
   ↓
Persistence Comparison
   ↓
Promotion Gate
```

---

## Decision 094 — Never Allow Retraining to Overwrite Production Directly

**Status:** Final — Implemented

### Decision

A retrained model first becomes a candidate.

It does not directly overwrite production.

### Reason

Training and deployment are separate decisions.

The architecture therefore maintains:

```text
Training
   ↓
Candidate
   ↓
Evaluation
   ↓
Promotion
   ↓
Production
```

---

## Decision 095 — Preserve Existing Service Boundaries

**Status:** Final — Implemented

### Decision

Phase 6 preserves the existing service boundaries:

```text
Next.js
   ↓
Express
   ↓
FastAPI
   ↓
MLflow / Model Registry
```

### Reason

Retraining and lifecycle management extend the existing architecture rather than replacing it.

This avoids unnecessary architectural rewrites and preserves the established application/inference boundary.

---

# 11. Phase 6 Production-Data Simulation Decisions

## Decision 096 — Use Controlled Production-Data Simulation

**Status:** Final — Implemented

### Decision

Because the project does not have live production telemetry, Phase 6 uses deterministic simulated production data derived from the processed historical dataset.

### Configuration

```text
Buildings: 12
Observations per building: 168
Total observations: 2016
Random seed: 42
```

Two scenarios are generated:

```text
Normal Production Scenario
Shifted Production Scenario
```

### Reason

This allows the lifecycle to be exercised without falsely representing historical data as live production telemetry.

---

## Decision 097 — Use Controlled Distribution Shift

**Status:** Final — Implemented

### Decision

The shifted scenario introduces deterministic changes to selected environmental and energy variables.

The shifted scenario includes:

* increased air temperature
* increased dew temperature
* increased wind speed
* increased target energy consumption

### Reason

A controlled shift provides a reproducible environment for testing monitoring and candidate-retraining behavior.

---

## Decision 098 — Preserve Persistence Strength During Simulation

**Status:** Final — Implemented

### Decision

The production-data simulation intentionally preserves a strong persistence relationship rather than altering the simulation to guarantee learned-model superiority.

### Reason

The purpose of the lifecycle demonstration is to evaluate candidates honestly.

The simulation must not be engineered solely to force a learned model into production.

The baseline remains meaningful even under the shifted scenario.

---

# 12. Candidate Training Decisions

## Decision 099 — Train Candidates from the Retraining Workflow

**Status:** Final — Implemented

### Decision

Phase 6 candidate training is implemented through:

```text
scripts/retrain_candidate.py
```

using the controlled production-data scenarios.

### Reason

Candidate training must be separate from the original historical baseline training workflow.

This provides an explicit retraining path.

---

## Decision 100 — Track Retraining Candidates in a Separate MLflow Experiment

**Status:** Final — Implemented

### Decision

Candidate retraining uses:

```text
building-energy-retraining
```

as the MLflow experiment.

### Reason

Retraining experiments should be distinguishable from the original Phase 1 model-development experiment.

---

## Decision 101 — Register Retrained Models Without Assigning Production

**Status:** Final — Implemented

### Decision

Candidate versions are registered in:

```text
building-energy-forecast
```

but candidate registration does not assign the production alias.

### Reason

Registration and production deployment are separate lifecycle actions.

---

## Decision 102 — Preserve Candidate Lineage

**Status:** Final — Implemented

### Decision

Candidate runs retain lifecycle metadata identifying:

* retraining origin
* source scenario
* model family
* candidate status
* validation status

### Reason

A future reviewer must be able to distinguish original trained models from retraining candidates.

---

# 13. Candidate Evaluation and Promotion Decisions

## Decision 103 — Evaluate All Retraining Candidates Before Promotion

**Status:** Final — Implemented

### Decision

Each Phase 6 candidate is evaluated before any promotion decision is considered.

Candidates:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

### Reason

The lifecycle must evaluate candidates independently rather than promoting the first successfully trained model.

---

## Decision 104 — Compare Candidates with Persistence on the Same Evaluation Population

**Status:** Final — Implemented

### Decision

Candidate performance and persistence performance are evaluated on the same Phase 6 evaluation population.

### Reason

The comparison must be internally consistent.

The project does not use a historical aggregate baseline metric as if it were directly interchangeable with a candidate metric calculated on a different evaluation population.

---

## Decision 105 — Do Not Promote a Candidate That Fails the Persistence Guard

**Status:** Final — Implemented

### Decision

A candidate that fails the persistence comparison is rejected.

### Reason

The project does not assume that learned-model complexity automatically creates operational value.

---

## Decision 106 — Final Phase 6 Candidate Outcome

**Status:** Final — Implemented

### Decision

The three Phase 6 candidates were evaluated on the shifted production-data scenario.

Results:

```text
v4 — Ridge
Candidate NMAE: 13.008031

v5 — Random Forest
Candidate NMAE: 9.466449

v6 — HistGradientBoosting
Candidate NMAE: 2.904410

Persistence
NMAE: 0.219467
```

None of the candidates beat persistence on this evaluation population.

Therefore:

```text
v4 → REJECTED
v5 → REJECTED
v6 → REJECTED
```

### Reason

The project must preserve the measured outcome rather than manufacture a successful learned-model promotion.

---

## Decision 107 — Keep the Production Alias Empty When No Learned Candidate Qualifies

**Status:** Final — Implemented

### Decision

No learned model owns the production alias after Phase 6.

Final state:

```text
Learned Production Model
None

Production Alias
None
```

### Reason

The absence of a qualifying learned candidate is a valid lifecycle state.

The system must not create a false production state simply to demonstrate promotion.

---

## Decision 108 — Serve Persistence When No Learned Production Model Exists

**Status:** Final — Implemented

### Decision

The FastAPI model service serves persistence when the MLflow registry has no valid learned production alias.

Final serving state:

```text
serving_mode = baseline
model_name = persistence
model_version = baseline
```

### Reason

The application remains operational while preserving the integrity of the model-promotion gate.

---

# 14. Rollback Decisions

## Decision 109 — Implement Rollback Through the Production Alias

**Status:** Final — Implemented

### Decision

Rollback is implemented by moving the MLflow `production` alias to a validated registered model version.

### Lifecycle

```text
Current Production
       ↓
Operational Issue
       ↓
Known Registered Version
       ↓
Validation
       ↓
@production Alias
       ↓
FastAPI
```

---

## Decision 110 — Validate Rollback Targets

**Status:** Final — Implemented

### Decision

Rollback validates that:

* the target model version exists
* the target version is READY
* the target is not already production
* a learned production version currently exists

### Reason

Rollback must be a controlled operation rather than an arbitrary registry mutation.

---

## Decision 111 — Do Not Fake a Production State to Demonstrate Rollback

**Status:** Final — Implemented

### Decision

Rollback is not demonstrated by artificially assigning a model to production solely for demonstration purposes.

### Actual result

When rollback was tested while no learned production model existed, the system correctly returned:

```text
No learned production model currently exists.
Rollback cannot be demonstrated until a production alias exists.
```

### Reason

The safety behavior is itself part of the lifecycle implementation.

The project preserves the real final state instead of fabricating a production deployment.

---

# 15. Final Lifecycle Architecture Decisions

## Decision 112 — Separate Monitoring, Eligibility, Training, Evaluation and Promotion

**Status:** Final

### Decision

The completed architecture maintains explicit boundaries between:

```text
Monitoring
   ↓
Retraining Eligibility
   ↓
Candidate Training
   ↓
Experiment Tracking
   ↓
Candidate Evaluation
   ↓
Promotion Decision
   ↓
Production
```

### Reason

Each stage answers a different question.

```text
Monitoring:
"What is happening?"

Eligibility:
"Is there enough evidence to retrain?"

Training:
"Can we create a candidate?"

Evaluation:
"Does the candidate provide sufficient value?"

Promotion:
"Should this candidate become production?"
```

No stage silently performs the responsibility of another.

---

## Decision 113 — Preserve Candidate and Production Isolation

**Status:** Final

### Decision

Candidate models remain isolated from production until they pass the promotion gate.

### Reason

Candidate training must never silently alter the model currently serving users.

---

## Decision 114 — Preserve Reproducible Lifecycle Evidence

**Status:** Final

### Decision

The lifecycle preserves:

* MLflow experiment runs
* registered model versions
* candidate versions
* evaluation metrics
* baseline comparisons
* rejection state
* promotion metadata where applicable
* rollback metadata where applicable
* simulation scenarios

### Reason

A model lifecycle should be auditable rather than represented only by the currently loaded model.

---

## Decision 115 — Treat Rejection as a Valid ML Lifecycle Outcome

**Status:** Final

### Decision

Model rejection is considered a successful lifecycle outcome when evaluation criteria are not satisfied.

### Reason

The purpose of the lifecycle is to make a correct decision, not to guarantee promotion.

The final Phase 6 outcome demonstrates:

```text
Train
 ↓
Register
 ↓
Evaluate
 ↓
Compare
 ↓
Reject
 ↓
Preserve Existing Serving Strategy
```

This is preferable to promoting a model that failed the defined benchmark.

---

# 16. Final System State

## Decision 116 — Final Serving Strategy Is Persistence

**Status:** Final

### Decision

The completed system serves the persistence baseline.

```text
Serving Mode
baseline

Model Name
persistence

Model Version
baseline
```

### Reason

No Phase 6 learned candidate passed the persistence guard.

---

## Decision 117 — Learned Models Remain Versioned and Auditable

**Status:** Final

### Decision

The learned models remain available in MLflow for inspection and lifecycle history.

Current Phase 6 candidate versions:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

All three were rejected after evaluation.

### Reason

Rejection does not erase lifecycle evidence.

---

## Decision 118 — Do Not Redesign the Model Strategy After the Final Evaluation

**Status:** Final

### Decision

The final architecture is not changed merely because persistence remained stronger than the learned candidates.

### Reason

The observed evaluation result is part of the project's technical outcome.

Changing the simulation, evaluation strategy, or serving architecture solely to force a learned model into production would undermine the credibility of the lifecycle demonstration.

---

# 17. Final Product and Documentation Decisions

## Decision 119 — Keep Model Lab as the ML Lifecycle Interface

**Status:** Final

### Decision

Model Lab remains the product surface for:

* experiments
* model versions
* evaluation
* lifecycle metadata
* baseline comparison
* production/serving state

It does not become an arbitrary model-selection interface.

---

## Decision 120 — Keep Monitoring as the Operational Interface

**Status:** Final

### Decision

Monitoring remains the product surface for:

* service state
* prediction observations
* serving state
* data quality
* drift
* performance
* persistence comparison
* degradation evidence

---

## Decision 121 — Keep the Final Application Scope Focused

**Status:** Final

### Decision

The final application retains analytical surfaces that provide direct value:

```text
Overview
Buildings
Building Details
Consumption
Forecasts
Anomalies
Model Lab
Monitoring
```

### Reason

The product should demonstrate the complete building-energy intelligence workflow without adding screens that do not contribute meaningful functionality.

---

## Decision 122 — Keep the Architecture Documentation as a Permanent Reference

**Status:** Final

### Decision

The documentation describes the final system architecture rather than remaining a phase-by-phase implementation diary.

The architecture documentation covers:

* service boundaries
* data flow
* ML flow
* inference
* monitoring
* lifecycle
* Docker
* testing
* CI
* limitations
* final serving state

---

## Decision 123 — Preserve the Project's Historical Limitations

**Status:** Final

### Decision

The project documentation explicitly states that:

* BDG2 is historical
* the current platform does not consume live telemetry
* monitoring is locally maintained
* monitoring state is bounded and in-memory
* the platform is not cloud-scale
* Kubernetes is not used
* automatic autonomous retraining is not implemented
* automatic autonomous promotion is not implemented

### Reason

Technical credibility requires clear boundaries around what the project actually demonstrates.

---

# 18. Final Architecture Principle

## Decision 124 — Prefer Evidence Over Complexity

**Status:** Final

### Decision

The project prioritizes measured engineering behavior over adding complexity for appearance.

The governing principle is:

```text
Do not add infrastructure because it sounds impressive.

Add infrastructure when the system has a real engineering requirement for it.
```

The completed architecture therefore favors:

```text
Correctness
+
Reproducibility
+
Explicit Boundaries
+
Baseline Awareness
+
Testing
+
Observability
+
Controlled Lifecycle Decisions
```

---

# 19. Final Lifecycle Contract

## Decision 125 — The Complete ML Lifecycle Is Controlled End-to-End

**Status:** Final

### Decision

The completed lifecycle is:

```text
NEW / INCOMING DATA
        ↓
VALIDATION
        ↓
MONITORING
        ↓
DATA QUALITY
DRIFT
PERFORMANCE
SERVICE HEALTH
        ↓
SUSTAINED DEGRADATION
        ↓
RETRAINING ELIGIBILITY
        ↓
CANDIDATE TRAINING
        ↓
MLFLOW EXPERIMENT
        ↓
REGISTERED CANDIDATE
        ↓
CANDIDATE EVALUATION
        ↓
COMPARE WITH REQUIRED REFERENCES
        ↓
PROMOTION GATE
        │
        ├───────────────┐
        ▼               ▼
      REJECT          PROMOTE
        │               │
        │               ▼
        │        PRODUCTION ALIAS
        │               │
        │               ▼
        │        PRODUCTION MODEL
        │               │
        └───────────────┘
                        ↓
                    INFERENCE
                        ↓
                   MONITORING
```

The lifecycle is controlled at every transition.

---

# 20. Final Project Outcome

## Decision 126 — The Project Ends with a Valid Baseline-Serving State

**Status:** Final

### Decision

The completed Building & Energy Intelligence Platform ends with:

```text
Historical BDG2 Data
        ↓
Validation
        ↓
Feature Engineering
        ↓
ML Training
        ↓
MLflow
        ↓
Model Registry
        ↓
Controlled Candidate Retraining
        ↓
Candidate Evaluation
        ↓
Persistence Comparison
        ↓
Candidate Rejection
        ↓
Persistence Serving
        ↓
Monitoring
```

### Final learned-model state

```text
v4 — Ridge
REJECTED

v5 — Random Forest
REJECTED

v6 — HistGradientBoosting
REJECTED
```

### Final production state

```text
Learned Production Model
None

Production Alias
None

Serving Strategy
Persistence Baseline

Serving Mode
baseline
```

### Final lifecycle conclusion

The project does not claim that a learned model is production-ready when the completed evaluation did not establish that result.

The final state is therefore:

```text
Trained Models
      ↓
Versioned
      ↓
Evaluated
      ↓
Compared Against Baseline
      ↓
Rejected Where Necessary
      ↓
Operational Baseline Preserved
```

This is the final model lifecycle outcome.

---

# 21. Final Engineering Record

The completed platform demonstrates:

```text
Data Engineering
        ↓
Feature Engineering
        ↓
Machine Learning
        ↓
Inference Service
        ↓
Application API
        ↓
Web Application
        ↓
Docker
        ↓
MLflow
        ↓
Model Registry
        ↓
Model Evaluation
        ↓
Baseline-Aware Promotion
        ↓
Operational Monitoring
        ↓
Data Quality Monitoring
        ↓
Drift Detection
        ↓
Performance Monitoring
        ↓
Sustained Degradation Detection
        ↓
Retraining Eligibility
        ↓
Controlled Candidate Retraining
        ↓
Experiment Tracking
        ↓
Candidate Evaluation
        ↓
Candidate Rejection / Promotion
        ↓
Rollback Capability
        ↓
Final Controlled Serving
```

The completed repository therefore represents a complete local MLOps demonstration rather than only an ML model.

---

# 22. Final Non-Negotiable Lifecycle Rules

The final system follows these rules:

```text
1. A trained model is not automatically a production model.

2. A registered model is not automatically a production model.

3. A candidate is isolated from production.

4. Candidate evaluation occurs before promotion.

5. Persistence remains the operational benchmark.

6. A learned model must satisfy the defined baseline-aware promotion gate.

7. A failed candidate is rejected rather than force-promoted.

8. Drift does not independently trigger retraining.

9. Data-quality problems are evaluated separately from model degradation.

10. Short-lived performance degradation does not qualify as sustained degradation.

11. Sufficient observations are required before degradation decisions.

12. Retraining eligibility does not itself modify production.

13. Candidate training does not modify production.

14. Evaluation does not automatically modify production.

15. Promotion is an explicit lifecycle action.

16. Production state is represented through MLflow lifecycle state.

17. Rollback targets must be valid registered model versions.

18. Rollback is not fabricated when no learned production model exists.

19. Monitoring does not unnecessarily break valid inference.

20. Historical data is not represented as live telemetry.

21. The current project is local-first and CPU-first.

22. The project does not introduce infrastructure without a genuine requirement.

23. Software correctness and predictive quality remain separate concerns.

24. The final measured lifecycle outcome is preserved rather than altered for presentation.
```

---

# Final Decision

The Building & Energy Intelligence Platform is complete.

Its final architecture is:

```text
DATA
 ↓
VALIDATION
 ↓
FEATURE ENGINEERING
 ↓
TRAINING
 ↓
EXPERIMENT TRACKING
 ↓
MODEL REGISTRY
 ↓
CONTROLLED EVALUATION
 ↓
PROMOTION / REJECTION
 ↓
SERVING
 ↓
MONITORING
 ↓
DRIFT / PERFORMANCE / DATA QUALITY
 ↓
SUSTAINED DEGRADATION
 ↓
RETRAINING ELIGIBILITY
 ↓
CANDIDATE TRAINING
 ↓
EXPERIMENT TRACKING
 ↓
CANDIDATE EVALUATION
 ↓
PROMOTION / REJECTION
 ↓
SERVING
 ↓
MONITORING
```

The final implementation deliberately ends with:

```text
Persistence Baseline
        ↓
Operational Serving
```

because the Phase 6 learned candidates did not satisfy the persistence-based promotion requirement.

No learned model is falsely represented as production.

No rollback state is fabricated.

No automatic retraining is claimed where controlled retraining was actually implemented.

No live telemetry capability is claimed where the project uses historical BDG2 data.

The decision log therefore records the final engineering truth of the project:

```text
Build the system.
Measure it.
Evaluate it.
Preserve the evidence.
Promote only when justified.
Reject when the evidence requires rejection.
Keep the system operational.
```

**This is the final decision record for the completed Building & Energy Intelligence Platform.**