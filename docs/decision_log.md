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
      ↓
Phase 5
Testability + CI + Observability
      ↓
Phase 6
Controlled Retraining
````

Phase 6 is the next planned lifecycle stage. Automatic retraining is not part of Phase 5.

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

## Decision 006 — Retain Learned Models as Evaluated Challengers

**Status:** Accepted

### Decision

Retain evaluated learned model families in the MLflow registry even when persistence performs better.

The current learned model families are:

```text
Ridge
Random Forest
HistGradientBoosting
```

### Reason

The project needs to demonstrate a complete learned-model lifecycle while preserving a meaningful baseline.

A learned model may be registered, evaluated, inspected, and rejected without being promoted to production.

This distinction is important:

```text
Benchmark Baseline:
Persistence

Evaluated Learned Models:
Ridge
Random Forest
HistGradientBoosting
```

Learned models must not be described as production models unless they pass the defined promotion gate.

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
* monitoring information

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

**Status:** Implemented

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

The current registry retains evaluated learned models and explicit lifecycle metadata.

---

## Decision 025 — Use MLflow as the Lifecycle Authority

**Status:** Implemented

### Decision

MLflow is the lifecycle authority for:

* experiment tracking
* registered model versions
* model artifacts
* lifecycle metadata
* model signatures
* aliases

### Reason

Model lifecycle state should not depend solely on local `.joblib` files.

MLflow provides a central local registry for the Dockerized system while preserving model lineage and version information.

Local model files remain useful for development and historical artifacts, but the Dockerized lifecycle path uses MLflow.

---

## Decision 026 — Record Reproducibility Metadata

**Status:** Implemented

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

**Status:** Implemented

### Decision

The persistence baseline remains part of the model evaluation and promotion process.

### Reason

A learned model should not be promoted merely because it performs better than other learned models.

The system must determine whether the learned candidate provides sufficient improvement over a simple operational benchmark.

The comparison must use the same evaluation criterion on both sides.

---

## Decision 028 — Use a Baseline-Aware Promotion Guard

**Status:** Implemented

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

**Status:** Implemented

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

**Status:** Implemented

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

**Status:** Implemented

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

**Status:** Implemented

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

**Status:** Implemented

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

**Status:** Implemented

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

**Status:** Implemented

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

**Status:** Implemented

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
* bounded in-memory monitoring state

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

**Status:** Completed

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

The following were intentionally deferred to Phase 5 or later:

* GitHub Actions CI
* automated monitoring
* data drift detection
* prediction-performance monitoring
* service observability
* automated retraining
* automated production promotion without evaluation
* cloud deployment
* Kubernetes
* distributed infrastructure
* large-scale LLM or agent infrastructure

---

# Phase 5 — Testability, CI and Observability

Phase 5 extends the platform from a functioning ML lifecycle into a system that can automatically verify its behavior and observe operational conditions.

The Phase 5 design principle is:

```text
Test
 ↓
Verify
 ↓
Observe
 ↓
Detect
 ↓
Decide
```

Phase 5 does not automatically retrain or automatically replace the serving model.

---

## Decision 043 — Treat Testing as a Multi-Layer System Concern

**Status:** Implemented

### Decision

Testing must cover multiple layers of the platform rather than only individual functions.

The testing strategy includes:

```text
Unit Tests
    ↓
Integration Tests
    ↓
API / Service Contract Tests
    ↓
Application Verification
    ↓
Build Verification
```

### Reason

An ML platform can fail even when individual functions work correctly.

Potential failures can occur at:

* data validation
* feature construction
* model behavior
* API contracts
* service integration
* application routes
* frontend behavior
* build boundaries

Testing must therefore reflect the architecture of the system.

---

## Decision 044 — Test Data Validation Explicitly

**Status:** Implemented

### Decision

Data validation behavior must be tested explicitly.

Validation areas include:

* required columns
* expected types
* null handling
* negative energy values
* duplicate timestamps
* timestamp ordering
* hourly frequency
* gaps
* building identity
* weather data assumptions
* target alignment

### Reason

Data errors can propagate into feature engineering and model performance.

The system should detect invalid assumptions before they silently affect downstream components.

---

## Decision 045 — Test Feature Construction for Temporal Correctness

**Status:** Implemented

### Decision

Feature construction must be tested for correctness and temporal integrity.

Important checks include:

* lag correctness
* rolling-window correctness
* required history length
* missing-history behavior
* feature schema
* prevention of future leakage

### Reason

Forecasting systems are especially vulnerable to temporal leakage and incorrect lag alignment.

A feature implementation that accidentally uses future information can produce misleading evaluation results while appearing technically correct.

---

## Decision 046 — Test Model Behavior Independently of Model Quality

**Status:** Implemented

### Decision

Model behavior tests should verify that inference produces structurally valid results without treating test execution as proof of model quality.

The tests cover behavior such as:

* prediction exists
* prediction is finite
* prediction is non-negative
* prediction is deterministic where expected
* model identity is returned
* model version is returned
* serving mode is represented
* baseline serving behaves correctly
* model input contracts remain compatible

### Reason

Software correctness and predictive quality are different concerns.

A model can produce technically valid predictions while still failing the baseline performance gate.

---

## Decision 047 — Test the Prediction API Boundary

**Status:** Implemented

### Decision

The prediction API must be tested with both valid and invalid requests.

The contract includes tests for:

* valid requests
* insufficient history
* duplicate observations
* invalid energy values
* invalid timestamps
* invalid weather values
* malformed payloads
* health endpoint
* readiness endpoint
* prediction response structure

### Reason

The model service is a critical boundary between application data and ML logic.

Invalid inputs should fail explicitly instead of producing ambiguous model behavior.

---

## Decision 048 — Test Application Integration Paths

**Status:** Implemented

### Decision

Major application paths should be covered by integration-oriented verification.

Important paths include:

* building data
* historical consumption
* forecast generation
* model lifecycle information
* anomaly information
* monitoring information

### Reason

The platform's value comes from the complete chain rather than isolated services.

A successful unit test suite is insufficient if the browser-to-API-to-model path is broken.

---

## Decision 049 — Use Automated CI Quality Gates

**Status:** Implemented

### Decision

Continuous integration must automatically verify the repository's core software quality checks.

The CI workflow includes appropriate checks for:

* Python tests
* Python linting
* API verification
* web verification
* builds
* relevant contracts

### Reason

Local verification alone cannot guarantee that future changes preserve repository health.

CI provides a repeatable gate before changes are considered integrated.

---

## Decision 050 — Treat Linting, Type Checking and Builds as Separate Signals

**Status:** Implemented

### Decision

Linting, type checking, and builds are treated as separate verification categories.

The distinction is:

```text
Lint
 ↓
Code-quality / static-rule verification

Typecheck
 ↓
Type correctness

Build
 ↓
Compilation / production artifact verification
```

### Reason

A successful build does not necessarily mean lint rules pass, and successful type checking does not necessarily mean code-quality rules pass.

The CI pipeline therefore should not collapse these checks into a single assumption.

---

## Decision 051 — Keep CI Focused on Fast, Deterministic Checks

**Status:** Accepted

### Decision

CI should prioritize checks that are deterministic and practical to run for normal repository changes.

These include:

* unit tests
* integration tests
* lint
* type checking
* core data validation
* feature tests
* API contracts
* application builds

### Reason

CI should provide fast feedback without making every change depend on expensive historical processing or complete infrastructure rebuilds.

Long-running tasks should remain scheduled, manual, or phase-specific where appropriate.

---

## Decision 052 — Separate Scheduled / Extended Validation from Normal CI

**Status:** Accepted

### Decision

Large or expensive validation tasks should not be required for every normal code change.

Potential extended tasks include:

* full historical data validation
* extended model evaluation
* large drift analysis
* large integration suites
* full Docker stack validation
* expensive data processing

### Reason

The project should maintain strong verification without turning every development iteration into a long-running pipeline.

---

## Decision 053 — Add Operational Monitoring to the ML Service

**Status:** Implemented

### Decision

The model service records operational prediction information so that prediction behavior can be observed after inference.

Monitoring records include information such as:

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

An inference service that only returns predictions cannot explain how its predictions are behaving over time.

Recording prediction events establishes the foundation for:

* performance monitoring
* baseline comparison
* degradation detection
* future retraining eligibility

---

## Decision 054 — Keep Monitoring State Bounded

**Status:** Implemented

### Decision

Current monitoring state is bounded rather than allowing unbounded in-memory growth.

The performance-monitoring implementation uses a maximum observation capacity.

### Reason

The current system is a local development platform and does not yet require a persistent telemetry database.

A bounded state model prevents uncontrolled memory growth while remaining simple and deterministic.

Persistent operational storage can be introduced when the system genuinely requires long-term telemetry retention.

---

## Decision 055 — Distinguish Prediction Observations from Historical Dataset Rows

**Status:** Accepted

### Decision

A monitoring observation represents an operational prediction event and must not be confused with the historical training dataset.

### Reason

The development dataset contains:

```text
12 selected buildings
210,528 processed rows
```

whereas monitoring observations are generated when the running prediction service receives requests.

Therefore:

```text
Historical Dataset Row
≠
Monitoring Prediction Observation
```

Similarly:

```text
Building Count
≠
Monitoring Observation Count
```

This distinction is necessary when interpreting monitoring dashboards.

---

## Decision 056 — Separate Prediction Observations from Performance Observations

**Status:** Implemented

### Decision

A prediction observation is recorded when a prediction is produced.

A performance observation is created only when the corresponding actual outcome is available.

The relationship is:

```text
Prediction
    ↓
Prediction Observation
    ↓
Actual Outcome Available
    ↓
Performance Observation
```

### Reason

Prediction monitoring can begin immediately, but realized prediction error cannot be calculated without an actual outcome.

This prevents the system from presenting predictions as if their accuracy were already known.

---

## Decision 057 — Use the Persistence Baseline in Performance Monitoring

**Status:** Implemented

### Decision

Performance monitoring compares the served prediction strategy against persistence when actual outcomes are available.

The comparison uses the same observations and outcomes.

### Reason

A model's performance should be interpreted relative to a meaningful reference.

The monitoring layer therefore retains:

```text
Served Model
      vs
Persistence Baseline
```

This preserves the same baseline-aware principle used during model promotion.

---

## Decision 058 — Calculate Global and Per-Building Performance

**Status:** Implemented

### Decision

Performance monitoring should support both aggregate and per-building metrics.

The current metrics include:

* MAE
* RMSE
* NMAE
* persistence MAE
* persistence RMSE
* persistence NMAE

### Reason

Aggregate metrics can hide building-level differences.

A multi-building energy platform therefore needs the ability to determine whether performance degradation is broad or concentrated in particular buildings.

---

## Decision 059 — Require Sufficient Data Before Declaring Degradation

**Status:** Implemented

### Decision

Model degradation cannot be declared from a small number of performance observations.

The current configuration uses:

```text
Recent window size:          30 observations
Sustained windows required:  3
Minimum observations:       90
```

### Reason

Short-lived fluctuations should not automatically become lifecycle events.

The detector therefore requires enough observations to evaluate three sustained windows.

Fewer than 90 observations results in:

```text
insufficient_data
```

rather than a degradation conclusion.

---

## Decision 060 — Require Sustained Degradation Across Multiple Windows

**Status:** Implemented

### Decision

A degraded state requires the configured degradation condition to persist across all required performance windows.

The current structure is:

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
Sustained degradation evaluation
```

### Reason

A single bad window may represent noise, a temporary event, or data quality problems.

Sustained evidence is more appropriate for a future lifecycle decision.

---

## Decision 061 — Use Relative Performance Degradation Thresholds

**Status:** Implemented

### Decision

The current degradation detector uses a relative threshold of:

```text
10%
```

for evaluating degradation against the relevant reference performance.

### Reason

Absolute error values vary across buildings and consumption scales.

A relative threshold provides a more interpretable basis for detecting deterioration across heterogeneous buildings.

---

## Decision 062 — Introduce Reference-Based Drift Monitoring

**Status:** Implemented

### Decision

Feature drift is evaluated by comparing current observations against reference feature distributions.

The conceptual relationship is:

```text
Reference Feature Distribution
             +
Current Feature Distribution
             ↓
        PSI Analysis
             ↓
      Drift Monitoring
```

### Reason

Changes in incoming feature distributions can indicate that the environment seen by the model differs from the development reference population.

Drift is therefore useful as an operational signal.

---

## Decision 063 — Use PSI for Current Drift Measurement

**Status:** Implemented

### Decision

Population Stability Index (PSI) is used for the current feature-drift implementation.

The current thresholds are:

```text
Healthy:  PSI < 0.10
Warning:  0.10 <= PSI < 0.25
Critical: PSI >= 0.25
```

### Reason

PSI provides a compact distribution-comparison measure suitable for the current numerical feature monitoring layer.

The implementation uses reference-derived quantile bins and handles finite-value filtering explicitly.

---

## Decision 064 — Require Minimum Drift Sample Counts

**Status:** Implemented

### Decision

A minimum of 30 current observations is required before a feature drift result becomes evaluable.

### Reason

A single prediction contains only one current value for a feature.

Treating such a value as a meaningful distribution change would create false signals.

The system therefore returns:

```text
insufficient_data
```

when the current sample count is below the configured minimum.

---

## Decision 065 — Treat Missing Reference Data Explicitly

**Status:** Implemented

### Decision

Drift monitoring must distinguish between:

```text
reference unavailable
```

and:

```text
no drift detected
```

### Reason

The absence of a reference distribution is an infrastructure/data configuration condition, not evidence that the feature distribution is stable.

The monitoring result therefore records whether the reference profile is available.

---

## Decision 066 — Handle Optional Weather Fields Safely

**Status:** Implemented

### Decision

Optional weather fields must not cause monitoring instrumentation to fail when they are absent.

### Reason

Prediction requests can legitimately omit optional weather fields.

Monitoring must not turn a valid prediction request into a server error simply because an optional field is `None`.

The monitoring feature extraction therefore adds optional weather features only when values are present.

This preserves the primary prediction path:

```text
Valid Prediction Request
        ↓
Prediction
        ↓
Monitoring Instrumentation
```

without allowing optional monitoring metadata to break inference.

---

## Decision 067 — Keep Drift Separate from Retraining

**Status:** Accepted

### Decision

Feature drift does not independently trigger retraining.

### Reason

A distribution shift does not necessarily mean that predictive performance has degraded.

The intended lifecycle is:

```text
Feature Drift
      ↓
Monitoring Signal
      ↓
Combine with Performance
      ↓
Evaluate Sustained Degradation
      ↓
Retraining Eligibility
```

Drift is supporting evidence rather than an automatic retraining command.

---

## Decision 068 — Keep Data Quality Separate from Model Degradation

**Status:** Accepted

### Decision

Poor prediction performance must be interpreted alongside data quality.

The intended structure is:

```text
Poor Performance
      ↓
Check Data Quality
      │
      ├── Critical data-quality issue
      │        ↓
      │   Investigate data
      │
      └── Data quality acceptable
               ↓
        Evaluate degradation
```

### Reason

Invalid, incomplete, or malformed incoming data can cause poor predictions without indicating that the learned model itself has degraded.

Data-quality signals therefore provide necessary context for performance monitoring.

---

## Decision 069 — Monitor Service Health Separately from Model Quality

**Status:** Implemented

### Decision

Service availability and request behavior are treated as separate monitoring concerns from predictive performance.

Service-health monitoring covers operational information such as:

* request behavior
* errors
* latency
* health state
* readiness state
* dependency availability

### Reason

A model can be statistically healthy while the service is unavailable.

Conversely, the service can be healthy while the model's predictive performance deteriorates.

These are separate failure modes and should remain separately observable.

---

## Decision 070 — Do Not Treat Drift as a Failure by Itself

**Status:** Accepted

### Decision

A drift signal should not automatically be interpreted as model failure.

### Reason

Distribution change can occur without meaningful degradation in prediction quality.

The monitoring architecture therefore distinguishes:

```text
Data Drift
Model Performance
Data Quality
Service Health
```

rather than collapsing them into a single failure state.

---

## Decision 071 — Use Explicit Monitoring Severity States

**Status:** Implemented

### Decision

Monitoring signals use explicit states rather than vague textual warnings.

The general state model includes:

```text
Healthy
Warning
Critical
Insufficient Data
Reference Unavailable
```

### Reason

Explicit states make monitoring easier to display, test, aggregate, and consume programmatically.

They also allow later lifecycle logic to distinguish actionable conditions from incomplete evidence.

---

## Decision 072 — Keep Automatic Retraining Out of Phase 5

**Status:** Accepted

### Decision

Phase 5 must not automatically retrain models.

### Reason

Monitoring and retraining are separate lifecycle responsibilities.

Phase 5 establishes the evidence required for a future retraining decision:

```text
Observations
+
Performance
+
Drift
+
Data Quality
+
Service State
```

but does not automatically execute:

```text
Training
→
Evaluation
→
Promotion
```

That workflow belongs to Phase 6.

---

## Decision 073 — Establish a Structured Retraining Eligibility Contract

**Status:** Implemented as Phase 5 groundwork

### Decision

Phase 5 establishes the information required to determine whether a future model is eligible for retraining.

The intended evidence includes:

* sufficient observations
* sustained performance degradation
* supporting drift evidence where relevant
* learned model underperformance relative to persistence
* acceptable data quality
* operational service state

The future structured state should contain:

* model identity
* model version
* serving mode
* performance window
* sample count
* current performance
* reference performance
* persistence-baseline performance
* drift state
* data-quality state
* service-health state
* degradation state
* reasons

### Reason

Retraining should be based on explicit evidence rather than a single metric or arbitrary trigger.

---

## Decision 074 — Use a State-Based Monitoring-to-Retraining Flow

**Status:** Accepted

### Decision

The future lifecycle should progress through explicit evidence states:

```text
NORMAL
   ↓
SIGNALS
   ↓
CORRELATE
   ↓
SUFFICIENT EVIDENCE
   ↓
RETRAINING ELIGIBLE
   ↓
Phase 6
```

### Reason

A single monitoring event should not immediately cause a lifecycle transition.

State progression allows the system to accumulate evidence and distinguish transient signals from sustained problems.

---

## Decision 075 — Preserve the Current Serving Model Until a Candidate Passes Evaluation

**Status:** Accepted

### Decision

Monitoring or degradation detection must not directly replace the currently served model.

### Reason

The production serving strategy must remain stable until a replacement candidate passes the established evaluation and baseline gates.

The future lifecycle remains:

```text
Current Serving Strategy
        ↓
Monitoring
        ↓
Retraining Eligibility
        ↓
Candidate Training
        ↓
Evaluation
        ↓
Baseline / Production Comparison
        ↓
Promotion
        ↓
New Serving Strategy
```

This preserves controlled model lifecycle management.

---

## Decision 076 — Make Monitoring Observable Through the Application

**Status:** Implemented

### Decision

Monitoring information should be exposed through the service/API boundary and represented in the application dashboard.

The monitoring surface should make important operational information visible, including:

* current serving state
* model identity
* monitoring observations
* performance state
* drift state
* data-quality state
* service state
* alerts/signals where available

### Reason

Observability should be part of the product rather than remaining hidden inside service logs.

---

## Decision 077 — Keep Monitoring Secondary to the Forecasting Path

**Status:** Accepted

### Decision

Monitoring must not compromise the primary forecasting workflow.

### Reason

Forecast generation is the core product capability.

Monitoring is an observability layer around that capability.

Therefore:

```text
Prediction
    ↓
Primary functionality
    ↓
Monitoring
```

must be implemented so that monitoring failures do not unnecessarily break valid prediction requests.

This principle directly informed the handling of optional weather fields in monitoring instrumentation.

---

## Decision 078 — Verify the Dockerized Runtime After Significant Service Changes

**Status:** Implemented

### Decision

Changes to the model-service runtime should be verified in the Dockerized environment when they affect runtime behavior.

### Reason

The local virtual environment and Docker environment have different dependency and filesystem boundaries.

The project therefore verifies the actual Dockerized stack rather than assuming that local tests alone prove container correctness.

The current local stack consists of:

```text
Web
API
Model Service
MLflow
```

and the services have been verified running together through Docker Compose.

---

## Decision 079 — Rebuild Only the Changed Docker Service When Possible

**Status:** Accepted

### Decision

When a single service changes, rebuild that service rather than unnecessarily rebuilding the complete stack.

For example:

```text
docker compose build model-service
```

### Reason

The model-service image can be expensive to rebuild.

Rebuilding only the affected service:

* reduces build time
* reduces unnecessary network activity
* reduces dependency-resolution exposure
* preserves already-valid images for unchanged services

A full stack rebuild remains appropriate when multiple image definitions or shared build inputs require it.

---

## Decision 080 — Treat Dependency Resolution as a Reproducibility Concern

**Status:** Accepted

### Decision

Container dependency failures must be treated as reproducibility/build-system issues rather than automatically as application logic failures.

### Reason

The Python model service depends on a set of version ranges.

Dependency resolution can therefore fail even when the application code and local environment are working correctly.

The project should keep dependency constraints explicit and investigate container resolution failures independently from prediction logic.

---

## Decision 081 — Keep Phase 5 Testing Evidence Explicit

**Status:** Implemented

### Decision

Phase 5 completion must be supported by explicit verification evidence rather than assuming that successful implementation implies correctness.

The completed verification categories include:

```text
Python tests
Python lint
API typecheck
API build
Web lint
Web build
```

The full Python test suite currently reports:

```text
47 passed
```

### Reason

A project intended to demonstrate engineering maturity should be able to show that its major software layers were actually verified.

---

## Decision 082 — Keep the Current Monitoring Architecture Local and Simple

**Status:** Accepted

### Decision

Phase 5 monitoring remains local and lightweight rather than introducing a dedicated observability platform.

### Reason

The project is still designed to run on a normal development laptop.

The current architecture provides meaningful monitoring concepts without requiring:

* Kubernetes
* distributed tracing infrastructure
* external monitoring SaaS
* production-scale telemetry storage
* message queues
* streaming infrastructure

These can be introduced later if operational requirements justify them.

---

## Decision 083 — Preserve the Historical Dataset as the Reference Development Population

**Status:** Accepted

### Decision

The selected BDG2 development population remains the reference foundation for the current project.

The current scope is:

```text
12 buildings
17,544 rows per building
210,528 processed rows
2016-01-01 through 2017-12-31
```

### Reason

The project requires a stable development population for:

* feature engineering
* model evaluation
* baseline comparison
* reference distributions
* reproducibility

The historical reference population should not be silently changed while interpreting model or monitoring behavior.

---

## Decision 084 — Keep Historical Data, Operational Monitoring Data, and Model Metadata Separate

**Status:** Accepted

### Decision

The platform maintains separate conceptual boundaries for:

```text
Historical Analytical Data
Operational Monitoring Data
Model Lifecycle Metadata
```

### Reason

These data classes have different purposes and retention requirements.

The separation is:

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

This prevents monitoring state from being confused with training data and prevents model registry state from being treated as part of the raw dataset.

---

## Decision 085 — Keep the Persistence Baseline First-Class Across the Lifecycle

**Status:** Implemented

### Decision

Persistence remains a first-class reference during:

```text
Evaluation
Promotion
Serving
Performance Monitoring
Future Retraining Eligibility
```

### Reason

The baseline is not only a Phase 1 experiment.

It provides a consistent reference throughout the model lifecycle.

The system should therefore continue asking:

```text
Is the learned model actually better than persistence?
```

rather than assuming that learned-model deployment is inherently preferable.

---

## Decision 086 — Keep Model Lab and Monitoring as Separate Observability Surfaces

**Status:** Implemented

### Decision

Model Lab and Monitoring serve different observability purposes.

```text
Model Lab
    ↓
Model lifecycle / registry / experiments

Monitoring
    ↓
Runtime / prediction / drift / performance / service state
```

### Reason

Model lifecycle information and operational model behavior are related but distinct.

Keeping the surfaces separate avoids turning one dashboard into an overloaded representation of unrelated concerns.

---

## Decision 087 — Preserve Explicit Historical Limitations in Documentation

**Status:** Accepted

### Decision

Documentation must explicitly state that the current system uses historical BDG2 data and is not a live building telemetry platform.

### Reason

The application demonstrates an operational ML architecture, but its current data source ends in 2017.

It would be misleading to describe the current forecast as live telemetry-driven forecasting.

The project therefore distinguishes:

```text
Current:
Historical inference demonstration

Future:
Live operational telemetry
```

---

## Decision 088 — Do Not Introduce Production-Scale Infrastructure Prematurely

**Status:** Accepted

### Decision

The platform should not introduce production-scale infrastructure merely to make the architecture appear more advanced.

Examples include:

* Kubernetes
* cloud-native orchestration
* streaming systems
* distributed databases
* GPU infrastructure
* LLM infrastructure

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
```

over unnecessary infrastructure complexity.

Infrastructure should be introduced only when there is a genuine system requirement.

---

# Current Architecture Decision Summary

The decisions through Phase 5 establish the following architecture:

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
                  Persistence              MLflow
                   Baseline                  │
                                             ▼
                                      Model Registry
                                             │
                                             ▼
                                      Evaluation Gate
                                             │
                                             ▼
                                      Promotion Decision
                                             │
                                             ▼
                                        Model Serving
                                             │
                                             ▼
                                        Monitoring
                                    ┌────────┼────────┐
                                    │        │        │
                                    ▼        ▼        ▼
                                  Drift  Performance  Service
                                    │        │        │
                                    └────────┼────────┘
                                             │
                                             ▼
                                      Future Eligibility
                                             │
                                             ▼
                                      Phase 6 Retraining
```

The architecture remains intentionally simple enough to run locally while providing explicit boundaries for future MLOps capabilities.

---

# Current Phase 5 Decision State

Phase 5 establishes:

```text
Testing
  ↓
Automated Verification
  ↓
CI
  ↓
Operational Monitoring
  ↓
Data Quality
  ↓
Drift Detection
  ↓
Performance Monitoring
  ↓
Service Health
  ↓
Sustained Degradation Detection
  ↓
Retraining Eligibility Evidence
```

The system does not automatically execute:

```text
Retraining
```

or:

```text
Production Promotion
```

as part of Phase 5.

Those actions remain controlled lifecycle decisions for Phase 6.

---

# Phase 5 Completion Principles

The completed Phase 5 architecture follows these principles:

```text
1. Test before trusting
2. Validate data before interpreting model behavior
3. Separate software correctness from model quality
4. Compare learned models with a meaningful baseline
5. Monitor data as well as predictions
6. Require sufficient observations before drawing conclusions
7. Require sustained degradation rather than single-event triggers
8. Treat drift as supporting evidence
9. Treat data quality separately from model degradation
10. Keep service health separate from predictive performance
11. Never allow monitoring instrumentation to unnecessarily break inference
12. Do not automatically retrain in Phase 5
13. Do not automatically replace the serving strategy
14. Keep the platform local and reproducible
```

---

# Future Decisions — Phase 6

## Decision 089 — Controlled Retraining Must Begin from Explicit Eligibility

**Status:** Planned

### Decision

Phase 6 retraining should begin only when the Phase 5 monitoring layer produces sufficient evidence for retraining eligibility.

### Reason

Training should not be triggered merely because:

* drift exists
* one prediction is inaccurate
* one building behaves differently
* a temporary data-quality issue occurs

The future trigger should combine multiple signals.

---

## Decision 090 — Require Sufficient Observations Before Retraining

**Status:** Planned

### Decision

A future retraining workflow must require a sufficient number of valid observations before beginning candidate training.

### Reason

Training from an insufficient or unrepresentative operational window could produce a candidate that reflects temporary noise rather than meaningful system change.

---

## Decision 091 — Require Sustained Performance Degradation Before Retraining

**Status:** Planned

### Decision

Future retraining eligibility should require sustained performance degradation across the configured evaluation windows.

### Reason

The monitoring layer already distinguishes transient performance variation from sustained degradation.

The retraining workflow should consume that distinction rather than bypassing it.

---

## Decision 092 — Use Drift as Supporting Evidence for Retraining

**Status:** Planned

### Decision

Feature drift may support a retraining decision but should not independently trigger retraining.

### Reason

The presence of drift does not establish that model performance has become unacceptable.

Retraining should be based primarily on demonstrated predictive degradation with contextual evidence from drift and data quality.

---

## Decision 093 — Require Baseline-Aware Retraining Evaluation

**Status:** Planned

### Decision

Any retrained candidate must again be compared against the persistence baseline before promotion.

### Reason

Retraining should not bypass the original model-quality principle.

The future lifecycle remains:

```text
Candidate
   ↓
Evaluation
   ↓
Persistence Comparison
   ↓
Promotion Gate
   ↓
Serving
```

---

## Decision 094 — Do Not Allow Retraining to Overwrite Production Directly

**Status:** Planned

### Decision

A retrained model must first become an evaluated candidate.

It must not directly overwrite the current production serving state.

### Reason

Training and deployment are separate lifecycle decisions.

This preserves the controlled model-management architecture established in Phase 4.

---

## Decision 095 — Preserve Existing Service Boundaries During Future Expansion

**Status:** Planned

### Decision

Future infrastructure should preserve the current service boundaries unless there is a clear engineering reason to change them.

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
Testing
 ↓
CI
 ↓
Monitoring
 ↓
Degradation Detection
 ↓
Retraining
 ↓
Deployment
```

with each layer introduced only after the previous layer is sufficiently validated.

The current architecture intentionally preserves:

```text
Correctness
+
Reproducibility
+
Clear Boundaries
+
Baseline Awareness
+
Testability
+
Observability
+
Controlled Lifecycle Decisions

as the foundation for future development.