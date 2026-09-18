# Architecture

## Overview

The Building & Energy Intelligence Platform is a CPU-first machine-learning application that combines:

- historical energy data processing
- feature engineering
- machine-learning training and evaluation
- experiment tracking
- model registry and versioning
- controlled model lifecycle management
- FastAPI inference
- Node.js/Express application orchestration
- Next.js/React presentation
- anomaly detection
- data-quality monitoring
- feature-drift monitoring
- prediction-performance monitoring
- sustained degradation detection
- controlled retraining
- candidate evaluation
- model promotion and rejection
- rollback
- automated testing
- continuous integration
- Docker-based local deployment

The architecture is intentionally modular. Data processing, model development, model lifecycle management, inference, application logic, frontend presentation, and monitoring are separated so that changes in one layer do not require duplicating logic across the rest of the system.

The final system is a local, production-oriented MLOps demonstration rather than a cloud-scale production platform.

---

# Final System Architecture

```text
                              BUILDING & ENERGY
                           INTELLIGENCE PLATFORM
                                      │
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
             ▼                        ▼                        ▼
       DATA & ML                  APPLICATION              LIFECYCLE
       PIPELINE                   PLATFORM                 MANAGEMENT
             │                        │                        │
             ▼                        ▼                        ▼
       BDG2 Dataset             Next.js / React             MLflow
             │                        │                        │
             ▼                        ▼                        ▼
      Validation +              Express API             Experiment Runs
      Feature Engineering            │                        │
             │                        │                        ▼
             ▼                        │                  Model Registry
      Processed Dataset              │                        │
             │                        │                        ▼
             ▼                        │                 Candidate Models
      Training / Evaluation          │                        │
             │                        │                        ▼
             ▼                        │                Evaluation Gates
       Model Candidates              │                        │
             │                        │                        ▼
             ▼                        │                Promotion / Reject
           MLflow                    │                        │
             │                        │                        ▼
             └───────────────┐        │                 Production Alias
                             │        │                        │
                             ▼        ▼                        ▼
                         FastAPI ML Service ◄──────────── Model Loader
                             │
                 ┌───────────┼───────────┐
                 │           │           │
                 ▼           ▼           ▼
            Learned Model  Persistence  Serving State
                           Baseline
                 │           │           │
                 └───────────┼───────────┘
                             │
                             ▼
                         Prediction
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        Data Quality       Drift       Performance
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                     Sustained Degradation
                             │
                             ▼
                  Retraining Eligibility
                             │
                             ▼
                    Candidate Retraining
                             │
                             ▼
                       MLflow Run
                             │
                             ▼
                     Candidate Evaluation
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
               REJECT                 PROMOTE
                  │                     │
                  │                     ▼
                  │              Production Alias
                  │                     │
                  │                     ▼
                  │                New Production
                  │                     │
                  └──────────┬──────────┘
                             │
                             ▼
                         Monitoring
````

The architecture therefore forms a closed but controlled ML lifecycle:

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
SERVING
  ↓
MONITORING
  ↓
PERFORMANCE / DRIFT / QUALITY EVIDENCE
  ↓
RETRAINING ELIGIBILITY
  ↓
CANDIDATE TRAINING
  ↓
EXPERIMENT TRACKING
  ↓
CANDIDATE EVALUATION
  ↓
PROMOTION DECISION
  ├── REJECT
  │
  └── PROMOTE
        ↓
     PRODUCTION
        ↓
     INFERENCE
        ↓
     MONITORING
```

Monitoring does not directly replace a model. Retraining does not automatically promote a model. Candidate models remain isolated from production until the explicit evaluation gate is satisfied.

---

# Architectural Principles

## Separation of Concerns

Each major component has one primary responsibility.

### Frontend

Responsible for:

* presentation
* user interaction
* analytical visualization
* frontend state
* lifecycle and monitoring visualization

The frontend does not contain model-training logic or model-selection logic.

### Express Application API

Responsible for:

* application-level orchestration
* building metadata
* historical consumption access
* prediction-context preparation
* communication with the ML service
* anomaly analysis
* lifecycle information exposed to the application
* application-level error handling

### FastAPI ML Service

Responsible for:

* prediction request validation
* historical-context validation
* feature construction
* model loading
* serving-strategy selection
* inference
* prediction responses
* monitoring instrumentation
* drift calculations
* performance calculations
* degradation analysis
* lifecycle information

### MLflow

Responsible for:

* experiment tracking
* run metadata
* model artifacts
* registered model versions
* model signatures
* lifecycle metadata
* production alias management

### Lifecycle Layer

Responsible for:

* determining whether retraining is justified
* generating candidate models
* evaluating candidates
* comparing candidates with production and persistence where applicable
* enforcing promotion gates
* rejecting failed candidates
* promoting explicitly approved candidates
* providing rollback capability

### Monitoring Layer

Responsible for:

* prediction observations
* data-quality signals
* drift signals
* performance observations
* degradation evidence
* service-health signals

Monitoring is observational and evidence-producing. It does not independently modify production state.

---

# Service Boundaries

The application follows explicit service boundaries.

```text
Browser
   ↓
Next.js / React
   ↓
Express API
   ↓
FastAPI ML Service
   ↓
Serving Strategy
   ├── Learned Production Model
   └── Persistence Baseline
```

The ML lifecycle is separate from the request path:

```text
Training
   ↓
MLflow
   ↓
Model Registry
   ↓
Candidate Evaluation
   ↓
Promotion Decision
   ↓
Production Alias
   ↓
FastAPI Serving
```

Monitoring is connected to serving but remains independent of lifecycle mutation:

```text
Prediction
   ↓
Monitoring
   ├── Data Quality
   ├── Drift
   ├── Performance
   └── Service Health
          ↓
   Degradation Evidence
          ↓
Retraining Eligibility
          ↓
Candidate Training
```

---

# Data Architecture

## Source Dataset

The platform uses the Building Data Genome Project 2 (BDG2) dataset.

The data pipeline is:

```text
Raw BDG2 Data
      ↓
Validation
      ↓
Cleaning / Alignment
      ↓
Feature Engineering
      ↓
Processed Feature Dataset
```

The canonical processed dataset is:

```text
data/processed/phase1_features.parquet
```

The processed dataset is used for:

* ML development
* historical application analytics
* feature construction
* evaluation
* controlled production-data simulation

The current platform is based on historical BDG2 data and does not represent a live building telemetry deployment.

---

# Production-Data Simulation

Because the project does not connect to a live production telemetry system, Phase 6 uses a controlled production-data simulation layer.

The simulator:

```text
Processed Feature Dataset
        ↓
Select Recent Historical Window
        ↓
168 observations per building
        ↓
12 buildings
        ↓
2016 selected observations
        ↓
┌─────────────────────┬─────────────────────┐
│                     │                     │
▼                     ▼
Normal Scenario       Shifted Scenario
│                     │
│                     ├── Temperature shift
│                     ├── Dew-temperature shift
│                     ├── Wind-speed shift
│                     └── Target-energy shift
│
▼
Normal Production Data
                      ▼
                Shifted Production Data
```

The simulation is deterministic and uses seed `42`.

Generated datasets:

```text
data/interim/production/normal_production.parquet
data/interim/production/shifted_production.parquet
```

The shifted scenario is intentionally controlled so that monitoring and lifecycle behavior can be demonstrated without pretending that the project has a live production data source.

---

# Feature Engineering

Feature construction is shared conceptually between model development and inference.

The forecasting feature workflow combines:

```text
Building Metadata
        +
Weather Context
        +
Calendar / Time Information
        +
Historical Energy
        ↓
Feature Construction
        ↓
Prediction Features
```

The feature set includes information such as:

* building ID
* site ID
* primary use
* building area
* weather variables
* calendar features
* cyclical time features
* historical energy lags
* rolling energy statistics
* heating degree-hour features
* cooling degree-hour features

The inference service requires:

```text
168 hourly historical observations
+
building metadata
+
weather context
+
target timestamp
```

Feature parity is maintained between training and inference to reduce training-serving skew.

---

# Machine-Learning Architecture

The ML development workflow is:

```text
Processed Dataset
      ↓
Train / Validation / Test Split
      ↓
Feature Preprocessing
      ↓
Model Training
      ↓
Validation
      ↓
Test Evaluation
      ↓
Artifact Generation
      ↓
MLflow Run
      ↓
Registered Model Version
```

The evaluated learned model families are:

```text
Ridge
Random Forest
HistGradientBoosting
```

The operational benchmark is:

```text
Persistence
```

Persistence predicts the next-hour energy value using the most recently observed energy value.

The persistence baseline is a first-class component of the architecture rather than a disposable benchmark.

---

# Baseline Architecture

The system deliberately distinguishes between:

```text
Persistence Baseline
        │
        │ operational reference
        ▼
Learned ML Models
        │
        │ evaluated challengers
        ▼
Production Decision
```

A learned model is not promoted merely because it is the strongest learned model.

The production gate asks whether the learned candidate satisfies the required evaluation criteria, including comparison with persistence.

This prevents unnecessary replacement of a simple operational strategy with a more complex model that does not demonstrate sufficient value.

---

# MLflow Architecture

The platform uses MLflow for experiment tracking and model registry functionality.

Primary training experiment:

```text
building-energy-phase1
```

Retraining experiment:

```text
building-energy-retraining
```

Registered model:

```text
building-energy-forecast
```

MLflow stores information including:

* model parameters
* validation metrics
* test metrics
* dataset metadata
* configuration
* Git information
* model artifacts
* model signatures
* model-family information
* validation state
* lifecycle metadata
* promotion metadata
* rejection metadata
* baseline-comparison information

The registry provides versioned model artifacts and lifecycle state.

---

# Model Registry

The current registered learned models include:

```text
v1 — Ridge
v2 — Random Forest
v3 — HistGradientBoosting
```

Phase 6 candidate retraining produced:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

The Phase 6 candidates were evaluated independently and were not automatically promoted.

The final lifecycle state is:

```text
Learned Production Model
None

Operational Serving Strategy
Persistence Baseline
```

This is an intentional outcome of the promotion guard.

The project does not manufacture a successful learned-model deployment when the measured evaluation does not justify one.

---

# Model Inference Service

The ML service is located at:

```text
apps/model_service/
```

It is implemented with FastAPI.

Primary endpoints include:

```text
GET  /health
GET  /ready
POST /predict
```

The service also exposes monitoring and Model Lab information.

The prediction flow is:

```text
Prediction Request
      ↓
Schema Validation
      ↓
Historical Context Validation
      ↓
Feature Construction
      ↓
Serving Strategy
      ↓
┌────────────────────────────┐
│                            │
▼                            ▼
Learned Production Model     Persistence Baseline
│                            │
└──────────────┬─────────────┘
               ▼
      Structured Prediction
               ↓
      Monitoring Instrumentation
```

The serving strategy is explicit.

The model service does not silently substitute a failed or unavailable learned model.

---

# Serving State

The model loader supports two serving strategies:

```text
learned
baseline
```

A learned serving state corresponds to a valid MLflow production alias.

The baseline serving state is used when no learned production model is currently valid.

The final system currently operates as:

```text
serving_mode = baseline
model_name   = persistence
model_version = baseline
```

The persistence strategy uses:

```text
latest observed energy
        ↓
next-hour prediction
```

This allows the application to remain operational while preserving the integrity of the promotion gate.

---

# Application API Architecture

The Node.js/Express application is located at:

```text
apps/api/
```

Its internal architecture is:

```text
Routes
  ↓
Services
  ↓
Repositories
  ↓
Application Data / ML Service
```

This prevents route handlers from becoming responsible for all application logic and data access.

---

# Application API Routes

## Buildings

```text
GET /api/buildings
GET /api/buildings/:buildingId
```

Provides building discovery and metadata.

## Consumption

```text
GET /api/buildings/:buildingId/consumption
```

Provides historical energy consumption.

## Forecast

```text
GET /api/buildings/:buildingId/forecast
```

Prepares the prediction context and communicates with the FastAPI service.

## Anomalies

```text
GET /api/buildings/:buildingId/anomalies
```

Provides building-level statistical anomaly analysis.

## Model Lab

```text
GET /api/model-lab/summary
GET /api/model-lab/versions
GET /api/model-lab/runs
```

Provides application-facing visibility into:

* MLflow runs
* registered versions
* model families
* evaluation state
* lifecycle state
* promotion state
* rejection state
* persistence baseline
* serving state

Model Lab is an observability surface. It is not an alternative training system or an arbitrary user-controlled model selector.

---

# Application Repositories

Current repositories include:

```text
apps/api/src/repositories/

├── buildingRepository.ts
├── consumptionRepository.ts
└── predictionRepository.ts
```

### Building Repository

Provides building metadata access.

### Consumption Repository

Provides historical consumption access from the processed feature dataset.

### Prediction Repository

Prepares the historical and contextual information required by the inference service.

---

# Application Services

Current services include:

```text
apps/api/src/services/

├── buildingService.ts
├── consumptionService.ts
├── predictionService.ts
├── anomalyService.ts
└── modelLabService.ts
```

Responsibilities:

* `buildingService` — building application logic
* `consumptionService` — historical consumption logic
* `predictionService` — inference-service communication
* `anomalyService` — anomaly detection
* `modelLabService` — lifecycle and MLflow information integration

---

# Frontend Architecture

The frontend is located at:

```text
apps/web/
```

Technology:

* Next.js
* React
* TypeScript
* Tailwind CSS
* Recharts

The application route structure is:

```text
apps/web/src/app/

├── page.tsx
├── buildings/
│   ├── page.tsx
│   └── [buildingId]/
│       └── page.tsx
├── consumption/
│   └── page.tsx
├── forecasts/
│   └── page.tsx
├── anomalies/
│   └── page.tsx
├── model-lab/
│   └── page.tsx
└── monitoring/
    └── page.tsx
```

The centralized frontend API client is:

```text
apps/web/src/lib/api.ts
```

Shared components are located under:

```text
apps/web/src/components/
```

---

# Frontend Information Architecture

The final application provides the following analytical surfaces:

```text
Overview
│
├── Buildings
│   └── Building Details
│       ├── Building Profile
│       ├── Historical Consumption
│       └── Forecast
│
├── Consumption
│
├── Forecasts
│
├── Anomalies
│
├── Model Lab
│
└── Monitoring
```

## Overview

Provides a high-level entry point into the platform.

## Buildings

Provides the available building inventory and metadata.

## Building Details

Combines:

* building profile
* historical consumption
* forecast information

The consumption and forecast views are intentionally presented together because they represent related building-level analysis.

## Consumption

Provides historical energy analysis.

## Forecasts

Provides prediction-oriented analysis.

## Anomalies

Provides statistically unusual consumption behavior.

## Model Lab

Provides visibility into:

* experiments
* model versions
* model families
* metrics
* lifecycle state
* baseline comparison
* production state
* candidate state
* rejection state

## Monitoring

Provides operational visibility into:

* service health
* serving identity
* prediction observations
* data quality
* drift
* performance
* persistence comparison
* degradation state

---

# Anomaly Detection Architecture

Anomaly detection is implemented in the application API.

The current approach uses a robust rolling statistical method based on:

* rolling median
* Median Absolute Deviation (MAD)

The flow is:

```text
Historical Consumption
        ↓
Rolling Statistical Analysis
        ↓
Robust Deviation Measurement
        ↓
Anomaly Classification
        ↓
Building-Level Anomaly Response
        ↓
Anomalies UI
```

Anomaly detection is separate from the forecasting model lifecycle.

An anomaly does not automatically trigger retraining.

---

# Monitoring Architecture

Monitoring surrounds the inference path.

```text
Prediction Request
      ↓
Validation
      ↓
Prediction
      ↓
Monitoring
      ├── Data Quality
      ├── Drift
      ├── Prediction Observation
      ├── Performance
      └── Service Health
              ↓
       Degradation Analysis
```

Monitoring is intentionally separated from model replacement.

The system observes the prediction service without allowing a single noisy observation to modify production state.

---

# Data-Quality Monitoring

The monitoring layer evaluates conditions including:

* required fields
* data types
* missing values
* invalid energy values
* duplicate timestamps
* timestamp ordering
* expected temporal frequency
* gaps
* building identity
* weather-field validity

Data-quality status is kept separate from model performance.

This allows the system to distinguish:

```text
Bad Input Data
      vs
Model Degradation
```

A critical data-quality condition is therefore a lifecycle blocker rather than an automatic reason to retrain.

---

# Drift Monitoring

The platform uses reference-based feature drift detection with Population Stability Index (PSI).

The drift workflow is:

```text
Reference Feature Profile
        +
Recent Monitoring Features
        ↓
Distribution Comparison
        ↓
PSI
        ↓
Monitoring Status
```

Current PSI interpretation:

```text
Healthy:   PSI < 0.10

Warning:   0.10 <= PSI < 0.25

Critical:  PSI >= 0.25
```

Minimum current sample count:

```text
30 observations
```

The drift implementation also handles:

* insufficient samples
* unavailable reference data
* non-finite observations

Drift is a supporting lifecycle signal.

It does not independently trigger retraining.

---

# Prediction Monitoring

Each prediction can retain:

* building ID
* prediction timestamp
* predicted energy
* persistence baseline
* model name
* model version
* serving mode

The monitoring record identifies what was actually served.

A prediction observation is an operational event.

It is not treated as:

* a training row
* a building entity
* a historical dataset record

This separation prevents operational monitoring state from becoming mixed with the historical training dataset.

---

# Performance Monitoring

A prediction becomes a performance observation when the corresponding actual outcome is available.

The performance record includes:

* prediction
* actual value
* persistence baseline
* absolute error
* squared error
* building ID
* timestamp
* model identity
* serving mode

Metrics include:

* MAE
* RMSE
* NMAE
* persistence-baseline MAE
* persistence-baseline RMSE
* persistence-baseline NMAE

Performance can be evaluated globally and per building.

The central operational comparison is:

```text
Served Strategy
      vs
Persistence Baseline
```

on the same observed outcomes.

---

# Sustained Degradation Detection

The system distinguishes sustained degradation from isolated poor predictions.

Current configuration:

```text
Recent window size:       30 observations
Sustained windows:          3
Relative degradation:      10%
Minimum observations:      90
```

The evaluation therefore requires:

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

90 observations total
      ↓
Sustained Degradation Evaluation
```

The system recognizes:

```text
insufficient_data
healthy
degraded
```

### insufficient_data

There are not enough outcome observations to establish the required sustained evidence.

### healthy

There is sufficient evidence, but the sustained degradation condition is not satisfied.

### degraded

There is sufficient evidence and the required sustained windows satisfy the degradation condition.

Degradation is an evidence signal.

It does not directly replace a production model.

---

# Retraining Eligibility Architecture

Retraining eligibility is implemented as an explicit decision boundary.

The eligibility workflow is:

```text
Current Model
      +
Performance Evidence
      +
Drift Evidence
      +
Data Quality
      +
Service Health
      ↓
Retraining Eligibility Evaluation
```

The eligibility evaluator considers:

* sufficient completed observations
* sustained performance degradation
* comparison with persistence
* drift state
* data-quality state
* service state
* current serving identity

The important distinction is:

```text
Monitoring
    ↓
Evidence
    ↓
Eligibility Decision
    ↓
Candidate Training
```

and not:

```text
Drift
    ↓
Automatic Retraining
```

Retraining eligibility does not itself train a model.

---

# Candidate Retraining Architecture

Controlled retraining is implemented separately from production serving.

The retraining workflow is:

```text
Production-Like Data
      ↓
Validation / Preparation
      ↓
Candidate Training
      ↓
MLflow Experiment
      ↓
Candidate Model Versions
      ↓
Candidate Evaluation
```

The retraining experiment is:

```text
building-energy-retraining
```

Phase 6 generated three candidate versions:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

Each candidate is registered in MLflow.

Candidate training does not assign the production alias.

Therefore:

```text
Candidate
   ≠
Production
```

---

# Candidate Isolation

Candidate models remain isolated from serving.

```text
Candidate Training
      ↓
MLflow
      ↓
Registered Candidate
      ↓
Evaluation
      ↓
Promotion Decision
```

The FastAPI service does not automatically begin serving a newly trained candidate.

This prevents retraining from becoming automatic production replacement.

---

# Candidate Evaluation

Candidate evaluation is performed separately from candidate training.

The workflow is:

```text
Candidate Model
      ↓
Evaluation Dataset
      ↓
Candidate Prediction
      ↓
Candidate NMAE
      +
Production Comparison
      +
Persistence Comparison
      ↓
Promotion Gate
```

The Phase 6 shifted production-data evaluation produced:

```text
v4 | Ridge
candidate NMAE = 13.008031
persistence NMAE = 0.219467

v5 | Random Forest
candidate NMAE = 9.466449
persistence NMAE = 0.219467

v6 | HistGradientBoosting
candidate NMAE = 2.904410
persistence NMAE = 0.219467
```

None of the candidates beat persistence on this evaluation population.

Therefore all three Phase 6 candidates were rejected.

---

# Promotion Architecture

Promotion is controlled by an explicit evaluation gate.

```text
Registered Candidate
        ↓
Candidate Evaluation
        ↓
Compare Against Required References
        ↓
Promotion Gate
        │
        ├───────────────┐
        ▼               ▼
     PASS              FAIL
        │               │
        ▼               ▼
   Explicit           REJECT
   Approval             │
        │               ▼
        ▼          Production Unchanged
   Production
      Alias
```

A learned model cannot become production merely because:

* it was trained successfully
* it has the lowest learned-model error
* it is newer
* it is registered in MLflow

The evaluation gate must be satisfied.

---

# Baseline Promotion Guard

The persistence baseline remains part of the promotion decision.

The core rule is:

```text
Candidate learned model
        ↓
Compare with persistence
        ↓
Candidate must demonstrate better performance
        ↓
Promotion may proceed
```

This prevents the architecture from replacing a simple operational baseline with a more complex learned model without measured evidence.

---

# Final Promotion State

The final Phase 6 evaluation produced:

```text
v4 — REJECTED
v5 — REJECTED
v6 — REJECTED
```

The reason was:

```text
Candidate did not beat persistence baseline.
```

The final registry therefore has:

```text
Learned Production Alias
None

Operational Serving
Persistence Baseline
```

No learned model was artificially promoted.

This is an intentional lifecycle result.

The architecture therefore demonstrates both sides of model lifecycle management:

```text
Candidate Training
        ↓
Evaluation
        ↓
Candidate Rejection
```

and contains the mechanisms required for:

```text
Candidate Training
        ↓
Evaluation
        ↓
Promotion
        ↓
Production
```

when a future candidate actually satisfies the defined gates.

---

# Explicit Approval Boundary

Candidate evaluation and promotion are separate concepts.

Evaluation determines whether a candidate satisfies the technical gate.

Promotion changes the production alias.

The lifecycle therefore separates:

```text
Technical Evaluation
        ↓
Promotion Eligibility
        ↓
Explicit Promotion Action
```

This prevents evaluation code from silently changing production serving state.

---

# Rollback Architecture

Rollback is implemented through the MLflow production alias.

The intended rollback flow is:

```text
Current Production
       ↓
Operational Issue
       ↓
Select Known Registered Version
       ↓
Validate Target
       ↓
Move @production Alias
       ↓
FastAPI Loads Production Version
       ↓
Monitoring
```

Rollback validates:

* target version exists
* target version is READY
* target is not already production
* a learned production alias currently exists

The rollback script intentionally refuses to operate when no learned production model exists.

The final project was in exactly that state after Phase 6:

```text
Learned Production Alias
None
```

Therefore rollback was safety-validated but not artificially demonstrated by creating a fake production state.

This preserves lifecycle integrity.

---

# Production Model Loading

The model service obtains the learned production model through MLflow registry state when a valid production alias exists.

Conceptually:

```text
MLflow Model Registry
        ↓
@production
        ↓
Model Loader
        ↓
FastAPI
        ↓
Inference
```

If no learned production alias exists:

```text
MLflow Registry
        ↓
No Learned Production
        ↓
Serving Decision
        ↓
Persistence Baseline
```

This makes the production decision explicit and observable.

---

# Model Signatures

Registered model versions preserve MLflow model signatures.

The signatures describe the feature contract, including categories such as:

* building identifiers
* site identifiers
* primary-use information
* building-area information
* weather variables
* calendar features
* cyclical time features
* historical energy lag features
* rolling energy statistics
* heating degree-hour features
* cooling degree-hour features

The registered versions were verified against the Docker-hosted MLflow server.

This provides an additional integrity check between:

```text
Training
   ↓
Registered Artifact
   ↓
Inference Contract
```

---

# Docker Architecture

The local production-style runtime consists of four services:

```text
┌─────────────────────────────┐
│       Next.js / React       │
│           :3000             │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Node / Express        │
│           :4000             │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      FastAPI ML Service     │
│           :8000             │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│           MLflow            │
│           :5000             │
└─────────────────────────────┘
```

Docker Compose provides:

* service networking
* service startup ordering
* containerized execution
* persistent MLflow storage

---

# Container Responsibilities

## Web

```text
docker/web.Dockerfile
```

Responsible for the production Next.js application.

## API

```text
docker/api.Dockerfile
```

Responsible for the Node.js/Express application API.

## Model Service

```text
docker/model-service.Dockerfile
```

Responsible for:

* FastAPI
* inference
* feature construction
* model loading
* MLflow model access
* persistence serving
* monitoring
* drift
* performance
* degradation

## MLflow

```text
docker/mlflow.Dockerfile
```

Responsible for:

* experiment tracking
* model registry
* lifecycle metadata
* persistent MLflow state

MLflow data is stored through the Docker volume:

```text
mlflow-data
```

---

# Runtime Network

The browser-facing application is:

```text
localhost:3000
```

The application API is:

```text
localhost:4000
```

The model service is:

```text
localhost:8000
```

MLflow is:

```text
localhost:5000
```

Inside Docker Compose, the application API communicates with:

```text
http://model-service:8000
```

The model service communicates with:

```text
http://mlflow:5000
```

The browser does not communicate directly with the FastAPI model service.

---

# Runtime Request Flow

A normal prediction request follows:

```text
Browser
   ↓
Next.js
   ↓
Express API
   ↓
Prediction Service
   ↓
FastAPI /predict
   ↓
Schema Validation
   ↓
Feature Construction
   ↓
Serving Decision
   ↓
Learned Production Model
       OR
Persistence Baseline
   ↓
Prediction
   ↓
Monitoring Instrumentation
   ↓
Express Response
   ↓
Frontend
```

The primary application capability remains:

```text
Building Context
      ↓
Forecast
```

Monitoring instrumentation must not become a single point of failure for valid predictions.

---

# Monitoring Reliability Boundary

Optional monitoring information is handled safely.

The prediction path is conceptually:

```text
Request
  ↓
Validation
  ↓
Prediction
  ↓
Monitoring
```

not:

```text
Request
  ↓
Monitoring
  ↓
Prediction
```

This means a monitoring-data issue should not unnecessarily prevent a valid prediction from being produced.

---

# Monitoring Storage

The current monitoring implementation uses bounded in-memory state inside the model service.

The monitoring state contains information such as:

* prediction records
* performance observations
* service-health information
* monitoring summaries

The state is intentionally bounded so that it cannot grow without limit during local operation.

The architecture does not claim to provide durable, multi-instance production telemetry storage.

---

# Application Storage

The current architecture deliberately avoids introducing a dedicated application database.

Application data is represented through:

```text
Static application data
        +
Processed datasets
        +
MLflow storage
        +
Bounded monitoring state
```

Building metadata is stored under:

```text
apps/api/src/data/
```

The canonical processed feature dataset is:

```text
data/processed/phase1_features.parquet
```

Local model artifacts are stored under:

```text
models/
```

MLflow provides the registry representation and tracked artifacts required for model lifecycle management.

---

# Repository Structure

The final repository architecture is:

```text
building-energy-intelligence/
│
├── apps/
│   ├── web/
│   │   └── src/
│   │       ├── app/
│   │       ├── components/
│   │       └── lib/
│   │
│   ├── api/
│   │   └── src/
│   │       ├── data/
│   │       ├── repositories/
│   │       ├── routes/
│   │       └── services/
│   │
│   └── model_service/
│       ├── app/
│       └── requirements.txt
│
├── ml/
│   ├── ingestion/
│   ├── validation/
│   ├── features/
│   ├── training/
│   ├── evaluation/
│   ├── monitoring/
│   ├── lifecycle/
│   └── artifacts/
│
├── data/
│   ├── raw/
│   ├── interim/
│   │   └── production/
│   ├── processed/
│   └── reference/
│
├── models/
│
├── reports/
│   └── generated/
│
├── notebooks/
│
├── scripts/
│   ├── phase0_data_proof.py
│   ├── phase1_build_features.py
│   ├── phase1_train.py
│   ├── phase3_export_buildings.py
│   ├── simulate_production_data.py
│   ├── retrain_candidate.py
│   ├── promote_model.py
│   └── rollback_model.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data/
│
├── configs/
│
├── docker/
│   ├── web.Dockerfile
│   ├── api.Dockerfile
│   ├── model-service.Dockerfile
│   └── mlflow.Dockerfile
│
├── .github/
│   └── workflows/
│
├── docs/
│
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

# Testing Architecture

Automated verification covers the major system boundaries.

```text
Python
├── pytest
└── Ruff

Node API
├── TypeScript Typecheck
└── Production Build

Next.js Web
├── ESLint
└── Production Build

Docker
└── Runtime Verification
```

The Python tests cover areas including:

* data validation
* feature generation
* lag behavior
* rolling-window behavior
* missing-history handling
* model behavior
* inference contracts
* persistence behavior
* inference API
* monitoring
* drift
* performance
* degradation
* retraining eligibility
* production-data simulation

The final full Python test run completed with:

```text
64 passed, 2 warnings
```

Ruff completed successfully:

```text
All checks passed!
```

The API typecheck passed.

The frontend lint passed.

The frontend production build passed.

---

# Continuous Integration

GitHub Actions provides repository-level verification.

The CI architecture focuses on deterministic engineering checks:

```text
Python
├── pytest
└── Ruff

API
├── TypeScript typecheck
└── production build

Web
├── ESLint
└── production build
```

The CI system is intentionally not coupled to expensive full retraining or full Docker rebuilding on every commit.

The following are not required for every normal code change:

* complete historical retraining
* large-scale model evaluation
* full Docker stack rebuild
* large data ingestion
* production cloud deployment

This keeps regular repository verification practical.

---

# Error Handling Architecture

Errors are contained at service boundaries.

```text
FastAPI Failure
      ↓
Prediction Service
      ↓
Express Error Handling
      ↓
Structured API Error
      ↓
Frontend Error State
```

The frontend distinguishes states such as:

* loading
* unavailable data
* empty data
* unavailable forecast
* unavailable buildings
* unavailable anomaly analysis
* unavailable Model Lab
* unavailable monitoring information

Internal service implementation details are not exposed directly to the user interface.

---

# Lifecycle State Model

The architecture distinguishes the following conceptual states:

```text
TRAINED
   ↓
REGISTERED
   ↓
CANDIDATE
   ↓
EVALUATED
   ├── REJECTED
   │
   └── ELIGIBLE
          ↓
       APPROVED
          ↓
      PRODUCTION
          ↓
       MONITORED
          ↓
   POSSIBLE DEGRADATION
          ↓
   RETRAINING ELIGIBILITY
          ↓
      NEW CANDIDATE
```

A model can remain registered without ever becoming production.

This is an intentional property of the lifecycle.

---

# Production Safety Rules

The architecture enforces the following rules:

1. Training does not automatically change production.
2. Candidate registration does not automatically change production.
3. Drift does not independently trigger retraining.
4. Performance degradation does not independently replace a model.
5. Critical data-quality problems do not automatically trigger retraining.
6. Short-lived degradation does not qualify as sustained degradation.
7. Candidate evaluation occurs before promotion.
8. Persistence remains a required operational reference.
9. Failed candidates remain rejected rather than being forced into production.
10. Production state is changed through an explicit promotion operation.
11. Rollback targets must correspond to valid registered model versions.
12. A rollback is not attempted when no learned production model exists.
13. Monitoring remains separate from model lifecycle mutation.
14. The serving service does not train models.
15. The frontend does not select arbitrary production models.

---

# Final Lifecycle

The completed ML lifecycle is:

```text
                         NEW DATA
                            │
                            ▼
                       VALIDATION
                            │
                            ▼
                        MONITORING
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        Data Quality      Drift       Performance
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                  Sustained Evidence
                            │
                            ▼
                Retraining Eligibility
                            │
                            ▼
                 Candidate Retraining
                            │
                            ▼
                    MLflow Experiment
                            │
                            ▼
                   Candidate Registry
                            │
                            ▼
                  Candidate Evaluation
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
               REJECT               PROMOTE
                  │                   │
                  │                   ▼
                  │            Production Alias
                  │                   │
                  │                   ▼
                  │            New Production
                  │                   │
                  │                   ▼
                  └──────────────► INFERENCE
                                      │
                                      ▼
                                  MONITORING
```

The lifecycle is controlled rather than autonomous.

---

# Final Phase 6 Lifecycle Outcome

The completed retraining lifecycle was exercised using the controlled shifted production-data scenario.

Candidate versions generated:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

Candidate evaluation:

```text
v4 — candidate NMAE 13.008031
v5 — candidate NMAE 9.466449
v6 — candidate NMAE 2.904410

Persistence — NMAE 0.219467
```

All three candidates failed the persistence comparison on the Phase 6 evaluation population.

Therefore:

```text
v4 → REJECTED
v5 → REJECTED
v6 → REJECTED
```

The final production state is:

```text
Learned Production Model
None

Production Alias
None

Serving Mode
baseline

Serving Model
persistence
```

This is the final state of the project.

The lifecycle is complete even though the lifecycle outcome is rejection rather than learned-model promotion.

---

# Final Architectural Data Flow

The complete platform can therefore be understood through four connected flows.

## 1. Application Flow

```text
User
 ↓
Next.js / React
 ↓
Express API
 ↓
Application Services
 ↓
Repositories / ML Service
 ↓
Response
 ↓
Frontend Visualization
```

## 2. ML Development Flow

```text
BDG2
 ↓
Validation
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
```

## 3. Serving Flow

```text
Frontend
 ↓
Express
 ↓
FastAPI
 ↓
Serving Decision
 ├── Learned Production Model
 └── Persistence Baseline
 ↓
Prediction
 ↓
Monitoring
```

## 4. Lifecycle Flow

```text
Monitoring
 ↓
Performance / Drift / Quality Evidence
 ↓
Sustained Degradation
 ↓
Retraining Eligibility
 ↓
Candidate Training
 ↓
MLflow
 ↓
Candidate Evaluation
 ↓
Promotion Gate
 ├── Reject
 └── Promote
       ↓
   Production Alias
       ↓
     Serving
       ↓
   Monitoring
```

---

# Architectural Boundaries

The final system maintains these boundaries:

```text
Frontend
  │
  ▼
Application API
  │
  ▼
ML Inference Service
  │
  ├── Serving Strategy
  │
  ├── Monitoring
  │
  └── MLflow
         │
         ▼
    Model Registry
         │
         ▼
   Lifecycle Control
```

Training remains outside the runtime prediction path:

```text
Training
   ↓
MLflow
   ↓
Registry
   ↓
Evaluation
   ↓
Promotion
```

The frontend remains outside the model lifecycle control path:

```text
Frontend
   ↓
Application API
   ↓
Read Lifecycle Information
```

It does not directly train, promote, reject, or rollback models.

---

# CPU-First Design

The architecture is designed to run on a normal development laptop.

It intentionally avoids:

* GPU-dependent infrastructure
* large transformer models
* LLM serving
* autonomous agents
* distributed training
* Kubernetes
* unnecessary cloud infrastructure
* WebGL-based visualization
* excessive frontend dependencies

The design principle is:

```text
Make the system look and behave like a serious engineering product
without making the infrastructure unnecessarily expensive.
```

---

# Current Production Boundary

The platform is a production-oriented engineering demonstration, not a claim of production-scale deployment.

It currently does not provide:

* live building telemetry
* cloud deployment
* Kubernetes orchestration
* horizontally scaled inference
* persistent distributed monitoring storage
* autonomous retraining
* autonomous production promotion
* enterprise authentication
* multi-tenant isolation
* production alert delivery infrastructure

These are outside the implemented architecture.

The current architecture intentionally provides a complete local demonstration of:

```text
Data
 ↓
ML
 ↓
Experiment Tracking
 ↓
Model Registry
 ↓
Controlled Serving
 ↓
Monitoring
 ↓
Degradation Evidence
 ↓
Retraining Eligibility
 ↓
Candidate Training
 ↓
Candidate Evaluation
 ↓
Promotion / Rejection
 ↓
Rollback Capability
```

---

# Final Architecture Summary

The Building & Energy Intelligence Platform is structured as a layered MLOps application:

```text
                    ┌─────────────────────┐
                    │      BDG2 Data     │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Validation /        │
                    │ Feature Engineering │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Training /          │
                    │ Evaluation          │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │       MLflow        │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Model Registry      │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Lifecycle Gate      │
                    │ / Promotion Guard   │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ FastAPI ML Service  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Serving Strategy    │
                    │                     │
                    │ Learned Model       │
                    │        OR           │
                    │ Persistence         │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │     Prediction      │
                    └──────────┬──────────┘
                               ↓
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
   Data Quality             Drift             Performance
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Degradation         │
                    │ Analysis            │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Retraining          │
                    │ Eligibility         │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Candidate Training  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Candidate           │
                    │ Evaluation          │
                    └──────────┬──────────┘
                               ↓
                       ┌───────┴───────┐
                       ↓               ↓
                    REJECT          PROMOTE
                       │               │
                       │               ↓
                       │        Production Alias
                       │               │
                       └───────┬───────┘
                               ↓
                           Serving
                               ↓
                           Monitoring
```

The application layer sits across the serving and observability layers:

```text
                 Next.js / React
                        ↓
                  Express API
                        ↓
                 FastAPI ML Service
                        ↓
                 Model / Baseline
                        ↓
                    Prediction
                        ↓
                    Monitoring
```

The final architecture therefore provides a complete, controlled ML lifecycle without conflating:

```text
training
model management
serving
monitoring
retraining
promotion
rollback
```

Each remains an explicit architectural responsibility.

The final operational state is intentionally:

```text
Persistence Baseline → Serving
```

while the trained learned models remain versioned, evaluated, and auditable in MLflow.

That is the final architecture of the completed Building & Energy Intelligence Platform.