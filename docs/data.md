# Data

## Overview

The Building & Energy Intelligence Platform uses the Building Data Genome Project 2 (BDG2) as its historical development and evaluation data source.

The data layer transforms raw building, electricity, weather, and metadata sources into validated and engineered data that can be used consistently across:

- Machine-learning training.
- Model evaluation.
- Application data access.
- Prediction-time inference.
- Monitoring.
- Controlled retraining.
- Candidate evaluation.

The final data flow is:

```text
Raw BDG2 Data
      ↓
Data Validation
      ↓
Cleaning / Temporal Alignment
      ↓
Feature Engineering
      ↓
Processed Feature Dataset
      ↓
ML Training / Evaluation
      ↓
MLflow Tracking / Registry
      ↓
Model Serving
      ↓
Prediction
      ↓
Monitoring
      ↓
Data Quality / Drift / Performance Signals
      ↓
Retraining Eligibility
      ↓
Candidate Training / Evaluation
````

The data architecture intentionally separates:

* Raw source data.
* Processed analytical data.
* Application-facing metadata.
* Model artifacts.
* MLflow lifecycle metadata.
* Prediction-time inference context.
* Operational monitoring observations.
* Simulated production data.

The project is a historical, local ML platform rather than a live building-telemetry system.

---

# Source Dataset

The primary source dataset is the Building Data Genome Project 2 (BDG2).

The dataset provides building-level energy observations together with contextual information including:

* Electricity consumption.
* Building metadata.
* Weather information.
* Temporal information.

The project currently uses a selected subset of 12 buildings for development, evaluation, application demonstrations, and controlled local lifecycle experiments.

The selected subset keeps the development workload manageable while retaining multiple buildings and different building characteristics.

---

# Raw Data Layout

Raw BDG2 data is stored under:

```text
data/raw/bdg2/
```

The primary source files are:

```text
data/raw/bdg2/electricity_cleaned.csv
data/raw/bdg2/metadata.csv
data/raw/bdg2/weather.csv
```

These files form the source layer.

Raw source files are not modified directly by downstream application or model-serving code.

Transformations are performed through repository scripts so that the raw source remains an inspectable reference.

---

# Selected Buildings

The current development population contains 12 selected buildings:

```text
Bear_assembly_Angel
Bear_assembly_Beatrice
Bear_assembly_Danial
Bear_assembly_Diana
Bear_assembly_Genia
Bear_assembly_Harry
Bear_assembly_Jose
Bear_assembly_Roxy
Bear_assembly_Ruby
Bear_education_Alfredo
Bear_education_Alvaro
Bear_education_Arnold
```

The selected population contains:

```text
12 buildings
17,544 hourly observations per building
210,528 processed rows
```

The development dataset covers:

```text
2016-01-01 through 2017-12-31
```

The 12-building development population is a historical analytical scope.

It must not be interpreted as:

* A live production population.
* The number of runtime monitoring observations.
* The number of prediction events.
* The number of operational buildings currently connected to the system.

---

# Initial Data Audit

The initial data audit established the following characteristics for the selected development population:

| Check                             |     Result |
| --------------------------------- | ---------: |
| Buildings                         |         12 |
| Rows per building                 |     17,544 |
| Duplicate building/timestamp keys |          0 |
| Non-hourly intervals              |          0 |
| Target mismatches                 |          0 |
| Lag mismatches                    |          0 |
| Missing energy observations       |     18,169 |
| Missing target observations       |     18,178 |
| Start timestamp                   | 2016-01-01 |
| End timestamp                     | 2017-12-31 |

The audit established that the selected data has the expected hourly structure and that temporal features were aligned with the underlying observations.

Missing observations remain an explicit data-quality characteristic of the source rather than being treated as evidence that the source is complete.

---

# Canonical Processed Dataset

The canonical processed feature dataset is:

```text
data/processed/phase1_features.parquet
```

Current dataset dimensions:

```text
Rows:    210,528
Columns: 44
```

The dataset contains the engineered features required by the ML pipeline.

It is also used by the application API for:

* Historical consumption retrieval.
* Prediction-context retrieval.
* Building-level analytical views.

The Parquet format is used for the processed analytical layer because it provides efficient columnar access while remaining straightforward to inspect and reproduce locally.

---

# Feature Dataset

The processed dataset combines several categories of information.

## Energy History

Historical electricity consumption is used to construct temporal features such as:

* Lagged consumption.
* Recent consumption statistics.
* Rolling means.
* Rolling maximums.
* Other historical consumption context required by the feature pipeline.

These features provide information about recent building behaviour.

Historical energy features are particularly important because the prediction problem is one-step-ahead hourly energy forecasting.

---

## Weather

Weather information provides environmental context for building energy consumption.

Weather variables are incorporated into the feature dataset alongside building and temporal information.

Weather context is also part of the prediction-time request contract where required so that inference can reconstruct the feature semantics expected by the model.

---

## Building Metadata

Building metadata provides relatively static contextual information.

Relevant fields include:

* Site information.
* Primary use.
* Floor area.
* Timezone.
* Building characteristics.

The application-facing building catalog can additionally expose available metadata such as:

* Latitude.
* Longitude.
* Year built.
* Number of floors.
* Occupants.
* Energy Star score.
* EUI.
* Site EUI.
* Heating type.
* LEED level.

The exact availability of individual metadata fields depends on the source records.

---

## Calendar Features

Temporal features capture recurring consumption patterns.

These include calendar-derived information such as:

* Hour.
* Weekday.
* Day.
* Month.

Calendar features allow the learned models to represent systematic temporal consumption patterns.

---

## Degree-Hour Features

Heating and cooling degree-hour style features provide additional information about temperature-sensitive energy demand.

These features are derived from weather and temporal context.

---

# Lag and Rolling Features

The forecasting feature set uses historical energy observations to derive lagged and rolling features.

These features are generated from information that is available before the prediction target.

The inference service reconstructs the required features from supplied historical observations rather than accepting an opaque precomputed feature vector from the frontend.

The boundary is:

```text
Historical observations
        ↓
Feature construction
        ↓
Model-ready feature vector
```

This preserves the same feature semantics between model development and model serving.

---

# Forecast Target

The primary forecasting target is:

```text
target_next_hour_kwh
```

It represents next-hour electricity consumption associated with the current feature row.

Conceptually:

```text
Historical observations up to time t
                ↓
           Feature vector
                ↓
       target_next_hour_kwh
                ↓
      Energy consumption at t+1
```

The forecasting problem is therefore:

```text
One-step-ahead
Hourly
Building-level
Electricity-consumption forecasting
```

---

# Temporal Alignment

Temporal alignment is a critical data requirement.

The dataset is hourly.

Historical features must use only information that would have been available before the prediction timestamp.

The prediction context is conceptually:

```text
t-168 ... t-2  t-1   t
   │              │    │
   │              │    └── Current prediction context
   │              └────── Recent history
   └───────────────────── Historical window
```

The inference service requires 168 historical hourly observations.

This corresponds to:

```text
168 hours = 7 days
```

The 168-hour requirement is enforced at the model-service boundary.

The purpose is to prevent incomplete historical context from silently producing an invalid feature vector.

---

# Prediction-Time Data Contract

A prediction request requires:

```text
Target timestamp
+
Building metadata
+
Weather context
+
168 historical hourly observations
```

The application API obtains the relevant historical context from the processed dataset before sending the prediction request to the FastAPI model service.

The model service then:

1. Validates the request.
2. Validates the historical observations.
3. Verifies the required history.
4. Reconstructs the temporal features.
5. Combines the feature context with building and weather information.
6. Performs inference.
7. Records the prediction for monitoring.
8. Returns the prediction and serving identity.

The prediction response contains:

```text
building_id
timestamp
predicted_energy_kwh
model_name
model_version
```

The response therefore identifies whether the result came from a learned model or the persistence baseline.

---

# Missing Data

The initial audit identified missing electricity observations and corresponding missing target observations.

Missing values are therefore treated as explicit data-quality characteristics.

The project does not assume that the source dataset is perfectly complete.

Downstream feature construction and inference logic must preserve the assumptions established by the validated Phase 1 pipeline.

In particular, prediction-time history must contain sufficient valid observations for the required feature construction.

---

# Training / Inference Data Relationship

The same feature definitions are preserved conceptually between model development and model serving.

```text
Processed Historical Data
          ↓
       Features
       ↙       ↘
  Training    Inference
     ↓           ↓
 Evaluation   Prediction
     ↓
   MLflow
```

The training pipeline creates the feature representation used by model experiments.

The FastAPI inference service reconstructs the required feature representation from the supplied historical context.

This separation reduces the risk of training-serving feature mismatch.

---

# Application Data Access

The processed feature dataset also serves as an application data source.

The Express application API uses the dataset for:

* Historical consumption retrieval.
* Prediction-context retrieval.
* Application-level energy data access.

The application data path is:

```text
phase1_features.parquet
          ↓
Application Repository
          ↓
Application Service
          ↓
Express API
          ↓
Next.js
```

This is intentionally a simple local architecture.

A separate operational database is not required by the current application scope.

---

# Building Metadata for the Application

The application API uses an exported building metadata file:

```text
apps/api/src/data/buildings.json
```

The export is generated by:

```text
scripts/phase3_export_buildings.py
```

The relationship is:

```text
BDG2 Metadata
      ↓
Export Script
      ↓
buildings.json
      ↓
Express API
      ↓
Next.js
```

The exported catalog provides a stable application-facing representation of the selected buildings.

It does not replace the original BDG2 metadata.

---

# Data Ownership by Layer

| Layer                | Responsibility                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------ |
| `data/raw/`          | Original source data                                                                       |
| `data/processed/`    | Validated and engineered analytical datasets                                               |
| `data/interim/`      | Intermediate and simulated production data                                                 |
| `ml/`                | Data processing, feature engineering, training, evaluation, monitoring and lifecycle logic |
| `models/`            | Local serialized model artifacts where applicable                                          |
| `apps/api/src/data/` | Application-facing building metadata                                                       |
| Express API          | Historical data and prediction-context access                                              |
| FastAPI              | Prediction-time validation, feature construction and inference                             |
| MLflow               | Experiment, model-version and lifecycle metadata                                           |
| Monitoring state     | Prediction and performance observations                                                    |
| Next.js              | Presentation of API responses                                                              |

This separation prevents application code from becoming responsible for ML transformations and prevents model lifecycle metadata from being mixed with the raw data layer.

---

# Data Flow Through the Platform

The complete historical-data path is:

```text
BDG2 Raw Data
      ↓
Phase 1 Validation
      ↓
Feature Engineering
      ↓
phase1_features.parquet
      ├─────────────────────┐
      │                     │
      ▼                     ▼
ML Training            Application API
      │                     │
      ▼                     ▼
Evaluation             Historical Data
      │                     │
      ▼                     ▼
MLflow Tracking        Express API
      │                     │
      ▼                     │
Model Registry              │
      │                     │
      ▼                     │
FastAPI Model Service ──────┘
      │
      ▼
Prediction
      │
      ▼
Monitoring
      ├── Data Quality
      ├── Feature Drift
      ├── Performance
      └── Service Health
      │
      ▼
Next.js Dashboard
```

The data layer therefore supports both:

```text
Analytical / ML Path
```

and:

```text
Application / Product Path
```

while keeping their responsibilities separate.

---

# Production Simulation Data

The final Phase 6 lifecycle requires production-like incoming data without claiming that the historical BDG2 dataset is a live telemetry source.

The project therefore provides a deterministic production-data simulation.

The simulator uses:

```text
data/processed/phase1_features.parquet
```

as its source and selects:

```text
168 observations × 12 buildings
=
2016 observations
```

Two production scenarios are generated:

```text
Normal Production
Shifted Production
```

The outputs are:

```text
data/interim/production/normal_production.parquet
data/interim/production/shifted_production.parquet
```

The simulation is deterministic and uses a fixed seed.

---

# Normal Production Scenario

The normal scenario represents incoming production-like observations without a major controlled distribution shift.

It preserves the underlying target behaviour while applying small deterministic perturbations to selected weather inputs.

Its purpose is to provide a reproducible operational-data scenario for lifecycle testing.

---

# Shifted Production Scenario

The shifted scenario intentionally introduces controlled distribution changes.

The implemented shift includes:

* Air-temperature increase.
* Dew-temperature increase.
* Wind-speed scaling.
* Target-consumption increase.
* Small deterministic noise.

The purpose is not to claim that this is a realistic future building trajectory.

The purpose is to create a controlled test condition in which the monitoring and retraining lifecycle can be exercised reproducibly.

---

# Production Simulation and Historical Data Boundary

Simulated production data is not treated as a new real-world source dataset.

The relationship is:

```text
Historical BDG2 Data
        ↓
Controlled Simulation
        ↓
Production-Like Scenario
        ↓
Monitoring / Retraining Demonstration
```

This distinction is important.

The project does not claim to have a live production telemetry feed.

The simulation exists specifically to demonstrate the operational lifecycle locally.

---

# Training Data

The original Phase 1 training pipeline uses:

```text
data/processed/phase1_features.parquet
```

The learned model families are:

```text
Ridge
Random Forest
HistGradientBoosting
```

The baseline strategies are:

```text
Persistence
Previous Day
Previous Week
```

The persistence baseline is kept separate from learned models.

---

# Persistence Baseline

Persistence is a first-class benchmark and serving strategy.

The baseline implementation is:

```text
pred_persistence
```

Display name:

```text
Persistence
```

Strategy:

```text
Use the latest observed energy value
as the next-hour prediction.
```

Conceptually:

```text
Latest observed energy
          ↓
Next-hour prediction
```

Persistence is used consistently across:

* Model evaluation.
* Promotion decisions.
* Serving fallback.
* Performance monitoring.
* Retraining evaluation.

The persistence baseline is deliberately retained even though learned models are available.

A learned model must demonstrate sufficient value against this simple reference before becoming learned production.

---

# Baseline Results

Baseline results are stored in:

```text
reports/generated/phase1_baseline_results.csv
```

The baseline report contains the evaluated baseline strategies and their metrics.

The persistence strategy is:

```text
pred_persistence
```

The project does not treat the baseline as a learned ML model.

It is an explicit operational reference.

---

# Baseline-Aware Evaluation

The project distinguishes between:

```text
Learned-model performance
```

and:

```text
Baseline performance
```

The lifecycle is:

```text
Train Learned Models
        ↓
Evaluate Learned Models
        ↓
Compare Learned Candidates
        ↓
Compare Against Persistence
        ↓
Baseline Guard
        ↓
      ┌───────────────┐
      │               │
    Pass            Fail
      │               │
      ▼               ▼
Candidate         Reject Candidate
Eligible
      │
      ▼
Promotion Decision
```

A candidate is not promoted simply because it is the strongest among the learned models.

This ensures that model complexity must be justified against a simple forecasting strategy.

---

# Candidate Retraining Data

Phase 6 introduced a separate retraining-data path:

```text
data/interim/production/
```

Candidate training operates on explicitly selected production-like scenarios.

The retraining experiment is tracked separately in MLflow:

```text
building-energy-retraining
```

The retraining candidates generated from the shifted scenario were:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

These models are candidates only.

They do not automatically become production models.

---

# Candidate Data and Production Boundary

Candidate training follows:

```text
Production-Like Data
        ↓
Candidate Training
        ↓
MLflow Experiment
        ↓
Registered Candidate
        ↓
Candidate Evaluation
        ↓
Promotion / Rejection
```

The key boundary is:

```text
Candidate Data
      ≠
Production Serving State
```

Candidate training cannot directly overwrite the current serving strategy.

---

# Candidate Evaluation Data

The Phase 6 shifted production scenario was used for controlled candidate evaluation.

Candidate results were:

```text
v4 — Ridge
candidate NMAE = 13.008031

v5 — Random Forest
candidate NMAE = 9.466449

v6 — HistGradientBoosting
candidate NMAE = 2.904410
```

Persistence on the same evaluation scenario achieved:

```text
persistence NMAE = 0.219467
```

None of the Phase 6 candidates beat persistence.

The final lifecycle decision was therefore:

```text
v4 — REJECTED
v5 — REJECTED
v6 — REJECTED
```

No learned production alias was created.

Persistence remained the serving strategy.

This is the actual final data-and-model lifecycle outcome.

---

# MLflow and Data Reproducibility

MLflow provides experiment tracking and model-registry capabilities around the data pipeline.

The underlying processed dataset remains separate from MLflow.

MLflow records metadata associated with training runs, including relevant:

* Parameters.
* Metrics.
* Tags.
* Model identity.
* Dataset/reference information.
* Reproducibility information.
* Lifecycle state.
* Model signatures.

The relationship is:

```text
Dataset
   ↓
Training Configuration
   ↓
Training Run
   ↓
Metrics + Parameters + Metadata
   ↓
Registered Model Version
```

This provides a traceable connection between training data, experiment configuration, and model versions.

---

# Data and Model Versioning Boundary

The project distinguishes:

```text
Dataset / Data Reference
```

from:

```text
Model Version
```

A model version in MLflow does not mean that the underlying raw dataset has been independently versioned through a formal data-version registry.

Instead, training runs retain relevant dataset and reproducibility metadata.

This is the current implementation boundary.

---

# Model Signature and Feature Contract

MLflow-registered models expose input signatures describing their expected feature representation.

The model service uses the registered model signature when operating through MLflow to determine the expected feature columns.

The relationship is:

```text
Registered Model
      ↓
MLflow Signature
      ↓
Expected Feature Contract
      ↓
Inference Feature Construction
      ↓
Model Prediction
```

This reduces the risk of serving a feature vector whose structure differs from the model's registered training contract.

---

# Prediction Serving Data

The frontend does not construct the model's internal feature vector.

Instead:

```text
Application API
      ↓
Building Metadata
Weather Context
Historical Observations
      ↓
FastAPI
      ↓
Feature Construction
      ↓
Registered Model / Persistence
      ↓
Prediction
```

This keeps feature engineering behind the model-service boundary.

The frontend therefore depends on the prediction API rather than directly depending on the internal feature representation.

---

# Baseline Serving Data Path

When no learned production alias exists, the model service operates in baseline mode.

The decision path is:

```text
MLflow Production Alias Available?
             │
        ┌────┴────┐
       Yes        No
        │          │
        ▼          ▼
 Learned Model  Persistence
    Serving       Serving
```

In persistence serving mode:

```text
Latest observed historical energy
             ↓
      Next-hour prediction
```

The API identifies the serving state through:

```text
model_name
model_version
serving_mode
```

The final system state is:

```text
model_name    = persistence
model_version = baseline
serving_mode  = baseline
```

This prevents a persistence prediction from being represented as a learned production model.

---

# Data Quality Validation

Validation is a first-class stage in the data architecture.

The principle is:

```text
Raw Data
   ↓
Validate
   ↓
Transform
   ↓
Feature Engineering
   ↓
Model
```

Important validation areas include:

* Timestamp integrity.
* Hourly continuity.
* Duplicate keys.
* Missing values.
* Target alignment.
* Lag alignment.
* Building identity.
* Feature consistency.
* Historical-context sufficiency.
* Invalid input values.

The purpose is to establish explicit data assumptions before information enters downstream ML and application systems.

---

# Data Reproducibility

Major data transformations are represented as repository code.

Important scripts include:

```text
scripts/phase0_data_proof.py
scripts/phase1_build_features.py
scripts/phase3_export_buildings.py
scripts/simulate_production_data.py
```

The major relationships are:

```text
Raw BDG2
   ↓
Data Proof / Validation
   ↓
Feature Construction
   ↓
Processed Parquet
```

and:

```text
Processed / Source Metadata
   ↓
phase3_export_buildings.py
   ↓
buildings.json
```

and:

```text
Processed Feature Dataset
   ↓
simulate_production_data.py
   ↓
Normal / Shifted Production Data
```

The transformations are therefore reproducible and inspectable.

---

# Data Integrity and Service Boundaries

The frontend must not:

* Load raw BDG2 files.
* Construct internal ML feature vectors.
* Access model artifacts directly.
* Make model promotion decisions.

The Express API must not:

* Train models.
* Modify model artifacts.
* Decide independently that a candidate should be promoted.

The FastAPI model service must:

* Validate prediction requests.
* Construct inference features.
* Perform model or baseline inference.
* Expose serving identity.

The ML pipeline must not:

* Directly control the frontend.
* Depend on browser-specific behaviour.
* Modify raw source files.

The monitoring system must not:

* Modify raw training data.
* Directly promote a model.
* Directly retrain a model.
* Replace the serving strategy without an explicit lifecycle decision.

These boundaries keep the data flow understandable, reproducible, and testable.

---

# Data Quality Monitoring

Operational data-quality monitoring considers conditions including:

* Required fields.
* Data types.
* Missing values.
* Invalid energy values.
* Duplicate timestamps.
* Timestamp ordering.
* Expected temporal frequency.
* Gaps.
* Building identity.
* Weather-field validity.

The operational relationship is:

```text
Incoming Prediction Context
        ↓
Data-Quality Checks
        ↓
Monitoring Signal
        ↓
Prediction / Operational Analysis
```

Data-quality monitoring helps distinguish:

```text
Invalid / incomplete incoming data
```

from:

```text
Genuine model-performance degradation
```

A critical data-quality problem should therefore not automatically be interpreted as a reason to retrain the model.

---

# Drift Data Architecture

Feature drift monitoring compares current observations against a reference profile.

The reference profile is:

```text
configs/monitoring_reference.json
```

The flow is:

```text
Reference Feature Distribution
             +
Current Feature Observations
             ↓
          PSI Analysis
             ↓
        Drift Status
```

The current implementation uses Population Stability Index (PSI).

Thresholds are:

```text
PSI < 0.10
    → healthy

0.10 ≤ PSI < 0.25
    → warning

PSI ≥ 0.25
    → critical
```

A minimum of:

```text
30 current observations
```

is required before a drift decision is considered evaluable.

Fewer observations produce:

```text
insufficient_data
```

rather than an unsupported drift conclusion.

---

# Drift Feature Families

The drift layer can monitor relevant feature families including:

* Building characteristics.
* Calendar features.
* Historical energy features.
* Rolling energy features.
* Weather variables.
* Temperature-derived features.
* Degree-hour features.

Optional weather fields are handled safely.

A missing optional weather value does not cause monitoring instrumentation to break an otherwise valid prediction request.

---

# Drift and Retraining Boundary

Drift is a supporting signal.

The lifecycle is:

```text
Feature Drift
      ↓
Monitoring Signal
      ↓
Combine With Performance Evidence
      ↓
Evaluate Sustained Degradation
      ↓
Retraining Eligibility
```

Drift alone does not trigger retraining.

This is an explicit architectural rule.

A distribution change may be operationally meaningful without necessarily requiring a new model.

---

# Monitoring Data

Monitoring data is operational data generated around prediction events.

A prediction observation can contain:

```text
building_id
timestamp
prediction
persistence_baseline
model_name
model_version
serving_mode
```

When the corresponding actual outcome becomes available, a performance observation can contain:

```text
building_id
timestamp
prediction
actual
persistence_baseline
absolute_error
squared_error
model_name
model_version
serving_mode
```

The relationship is:

```text
Prediction Event
      ↓
Prediction Observation
      ↓
Actual Outcome Available
      ↓
Performance Observation
```

A monitoring observation is therefore a prediction event.

It is not:

* One building.
* One historical dataset row.
* One training sample.

---

# Monitoring Storage Strategy

The current monitoring implementation uses bounded in-memory state inside the model service.

The runtime monitoring state is bounded to:

```text
1000 observations
```

This keeps local runtime memory predictable.

The current monitoring state is not presented as a durable production telemetry database.

A persistent operational monitoring store would become appropriate if the platform required:

* Long-term telemetry retention.
* Multi-instance monitoring.
* Durable prediction history.
* Persistent alert history.
* Cross-process monitoring.
* Production-scale observability.

---

# Prediction and Actual-Outcome Relationship

Model-performance monitoring requires both:

```text
Prediction
+
Actual Outcome
```

The flow is:

```text
Prediction
    +
Actual Energy
    ↓
Performance Observation
    ↓
Error Calculation
    ↓
Rolling Performance Metrics
```

Without the actual outcome, the system can record the prediction event but cannot calculate realized forecasting error.

This distinction is important when interpreting monitoring observation counts.

---

# Performance Monitoring Data

Performance monitoring calculates:

* MAE.
* RMSE.
* NMAE.
* Persistence MAE.
* Persistence RMSE.
* Persistence NMAE.
* Building-level metrics.
* Model-versus-persistence comparisons.

The conceptual structure is:

```text
Prediction + Actual
        ↓
Absolute Error
        ↓
Squared Error
        ↓
Performance Metrics
        ↓
Global + Per-Building Analysis
```

The persistence baseline is calculated using the same actual outcomes so that the learned serving strategy and baseline can be directly compared.

---

# Performance Degradation Data

The current degradation configuration uses:

```text
Recent window size:          30 observations
Sustained windows required:  3
Relative degradation limit:  10%
Minimum observations:        90
```

The decision structure is:

```text
30 observations
      ↓
First window

30 observations
      ↓
Second window

30 observations
      ↓
Third window

90 observations
      ↓
Sustained degradation evaluation
```

Fewer than 90 outcome observations result in:

```text
insufficient_data
```

The detector distinguishes between:

```text
insufficient_data
healthy
degraded
```

A degraded state requires the configured sustained-degradation condition across the required windows.

---

# Baseline-Aware Performance Monitoring

Performance monitoring retains persistence as an operational reference.

The comparison is:

```text
Served Strategy
      vs
Persistence Baseline
```

using the same actual outcomes.

This provides a consistent reference for determining whether the current serving strategy continues to provide useful forecasting performance.

---

# Retraining Data Boundary

Controlled retraining is separated from ordinary historical data processing.

The final lifecycle is:

```text
Incoming / Simulated Production Data
        ↓
Validation
        ↓
Monitoring
        ↓
Performance / Drift Evidence
        ↓
Retraining Eligibility
        ↓
Candidate Training Data
        ↓
Candidate Model
        ↓
Candidate Evaluation
        ↓
Baseline / Production Comparison
        ↓
Promotion or Rejection
```

Retraining does not directly overwrite the production serving state.

A newly trained model remains a candidate until it passes the required evaluation gates.

---

# Retraining Eligibility Data Contract

The final eligibility decision combines multiple evidence sources.

Conceptually:

```text
Sufficient Observations
        +
Sustained Performance Degradation
        +
Baseline Comparison
        +
Data Quality Not Critical
        +
Service State Acceptable
        +
Supporting Drift Evidence
        ↓
Retraining Eligibility Decision
```

The eligibility decision contains information such as:

* Model identity.
* Model version.
* Serving mode.
* Sample count.
* Required sample count.
* Sustained degradation state.
* Current model NMAE.
* Persistence NMAE.
* Baseline comparison availability.
* Drift status.
* Data-quality status.
* Service status.
* Positive reasons.
* Blocking reasons.

Possible eligibility states are:

```text
retraining_eligible
not_eligible
```

Eligibility does not perform training.

It is the explicit boundary between monitoring evidence and candidate creation.

---

# Data and Lifecycle Separation

The completed system maintains three conceptually different categories of data:

```text
Historical Analytical Data
        +
Operational Monitoring Data
        +
ML Lifecycle Metadata
```

Historical analytical data includes:

* BDG2 source information.
* Processed features.
* Historical energy observations.
* Historical weather information.
* Building metadata.

Operational monitoring data includes:

* Prediction observations.
* Actual outcomes where available.
* Performance metrics.
* Drift signals.
* Data-quality signals.
* Service-health signals.

ML lifecycle metadata includes:

* Experiment runs.
* Model versions.
* Model signatures.
* Evaluation results.
* Candidate state.
* Rejection metadata.
* Promotion metadata.
* Rollback metadata.

These categories are intentionally kept separate.

---

# Current Historical Forecasting Limitation

The historical source data ends on:

```text
2017-12-31
```

The current application therefore demonstrates forecasting using historical building observations.

The project does not currently contain a live present-day building telemetry ingestion system.

The actual current architecture is:

```text
Historical Data
      ↓
Inference
      ↓
Monitoring
      ↓
Dashboard
```

Phase 6 adds simulated production-like data for lifecycle demonstration:

```text
Historical Data
      ↓
Controlled Simulation
      ↓
Production-Like Data
      ↓
Drift / Performance / Retraining Lifecycle
```

This must not be described as a real live production data feed.

---

# Current Storage Strategy

The project deliberately uses simple local storage mechanisms appropriate to its current scope.

Current storage includes:

```text
Raw CSV
   ↓
Processed Parquet
   ↓
JSON Application Metadata
   ↓
Local Model Artifacts / MLflow Models
   ↓
MLflow Metadata
   ↓
Bounded In-Memory Monitoring State
```

MLflow additionally stores:

```text
Training Runs
      ↓
Parameters
      ↓
Metrics
      ↓
Tags
      ↓
Model Artifacts
      ↓
Registered Versions
      ↓
Lifecycle Metadata
```

The architecture is intentionally:

* Local.
* Reproducible.
* Inexpensive.
* Inspectable.
* CPU-friendly.
* Laptop-runnable.

---

# Why No Operational Database?

A dedicated operational database is not required by the current completed scope.

The current system can use:

* Parquet for historical analytical data.
* JSON for the application building catalog.
* MLflow for experiment and model lifecycle state.
* Bounded in-memory state for runtime monitoring.

A database would become justified if the platform required persistent operational state such as:

* Large-scale prediction history.
* Long-term monitoring history.
* Alerts.
* User configuration.
* Multi-instance service operation.
* Persistent retraining records.
* High-volume production telemetry.

The current architecture therefore avoids introducing a database without an actual requirement for one.

---

# Data Validation Philosophy

The project's data philosophy is:

```text
Raw Data
   ↓
Validate
   ↓
Transform
   ↓
Feature Engineering
   ↓
Evaluate
   ↓
Serve
   ↓
Monitor
```

Important principles include:

1. Raw data remains inspectable.
2. Transformations are reproducible.
3. Data is validated before modeling.
4. Temporal causality is preserved.
5. Feature semantics remain consistent between training and serving.
6. Baselines remain first-class references.
7. Monitoring data remains separate from historical training data.
8. Data quality is distinguished from model degradation.
9. Drift is treated as evidence rather than an automatic retraining command.
10. Production-like simulation is explicitly distinguished from real production telemetry.

---

# Final Data Architecture

The final data architecture is:

```text
                         ┌─────────────────────┐
                         │     BDG2 Source     │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │    Raw CSV Data     │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Validation / Clean  │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Feature Engineering │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │ Processed Parquet   │
                         └──────────┬──────────┘
                                    │
                   ┌────────────────┴────────────────┐
                   │                                 │
                   ▼                                 ▼
          ┌─────────────────┐               ┌─────────────────┐
          │   ML Pipeline   │               │ Application API │
          └────────┬────────┘               └────────┬────────┘
                   │                                 │
                   ▼                                 ▼
          ┌─────────────────┐               ┌─────────────────┐
          │ Evaluation      │               │ Historical Data │
          └────────┬────────┘               └─────────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ MLflow          │
          │ Experiments     │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Model Registry  │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ FastAPI Service │
          └────────┬────────┘
                   │
                   ▼
               Prediction
                   │
                   ▼
          ┌─────────────────┐
          │   Monitoring    │
          └────────┬────────┘
                   │
          ┌────────┼────────┐
          ↓        ↓        ↓
       Quality   Drift  Performance
          │        │        │
          └────────┼────────┘
                   ↓
          ┌─────────────────┐
          │ Degradation     │
          │ Detection       │
          └────────┬────────┘
                   ↓
          ┌─────────────────┐
          │ Retraining      │
          │ Eligibility     │
          └────────┬────────┘
                   ↓
          ┌─────────────────┐
          │ Candidate Data  │
          └────────┬────────┘
                   ↓
          ┌─────────────────┐
          │ Candidate Model │
          └────────┬────────┘
                   ↓
          ┌─────────────────┐
          │ Evaluation      │
          └────────┬────────┘
                   ↓
          ┌─────────────────┐
          │ Promote /       │
          │ Reject          │
          └─────────────────┘
```

---

# Final Data Status

The completed data architecture supports:

* Historical energy analysis.
* Building-level analysis.
* Weather-aware forecasting.
* Feature-based ML experimentation.
* Baseline evaluation.
* Learned-model evaluation.
* Model serving.
* MLflow tracking.
* Model registration.
* Prediction monitoring.
* Data-quality monitoring.
* Feature-drift monitoring.
* Performance monitoring.
* Sustained degradation detection.
* Retraining eligibility.
* Controlled production-data simulation.
* Candidate retraining.
* Candidate evaluation.
* Baseline-aware promotion decisions.

The final system does not claim to provide:

* Live building telemetry.
* Real-time streaming ingestion.
* A production-scale data warehouse.
* A production-scale telemetry platform.
* Durable large-scale monitoring storage.
* Formal enterprise data versioning.
* Autonomous retraining.
* Autonomous model promotion.

These are explicit boundaries of the completed project.

---

# Final Data Principles

The final data architecture is governed by the following principles:

```text
Correctness
    +
Reproducibility
    +
Temporal Integrity
    +
Clear Data Boundaries
    +
Baseline Awareness
    +
Operational Observability
    +
Controlled Lifecycle Data
    +
Simple Local Infrastructure
```

The core relationship is:

```text
Historical Data
      ↓
Validated Features
      ↓
ML / Application
      ↓
Operational Observations
      ↓
Evidence
      ↓
Controlled Lifecycle Decision
```

The project does not treat every new observation as training data, every distribution change as a retraining requirement, or every trained model as a production model.

Instead, data moves through explicit contracts and decision boundaries.

---

# Final Data Lifecycle

The completed data lifecycle is:

```text
BDG2 Historical Source
        ↓
Raw Data
        ↓
Validation
        ↓
Temporal Alignment
        ↓
Feature Engineering
        ↓
Processed Feature Dataset
        ↓
Training / Evaluation
        ↓
MLflow Tracking
        ↓
Model Registry
        ↓
Inference
        ↓
Prediction Observations
        ↓
Actual Outcomes
        ↓
Performance Monitoring
        +
Feature Drift Monitoring
        +
Data Quality Monitoring
        ↓
Sustained Degradation Analysis
        ↓
Retraining Eligibility
        ↓
Controlled Production-Like Data
        ↓
Candidate Training
        ↓
Candidate Evaluation
        ↓
Persistence / Production Comparison
        ↓
Promotion or Rejection
```

The final Phase 6 evaluation resulted in candidate rejection and retention of the persistence serving strategy.

Therefore, the final operational data-and-serving state is:

```text
Historical Data
      ↓
Processed Features
      ↓
Inference
      ↓
Persistence Baseline Serving
      ↓
Monitoring
```

with the controlled retraining lifecycle available for future candidate evaluations.

This is the final data architecture and data-state definition for the completed Building & Energy Intelligence Platform.