# Data

## Overview

The Building & Energy Intelligence Platform uses the Building Data Genome Project 2 (BDG2) as its initial data source.

The data pipeline transforms raw building, electricity, weather, and metadata sources into a validated feature dataset that can be used consistently by model training, evaluation, application data access, prediction-time inference, and operational monitoring.

The current pipeline is:

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
Performance / Drift / Data Quality Signals
````

The data layer is intentionally designed around clear boundaries between:

* raw source data
* processed analytical data
* application-facing metadata
* model artifacts
* MLflow lifecycle metadata
* prediction-time inference context
* operational monitoring observations

---

# Source Dataset

The initial source is the Building Data Genome Project 2 (BDG2).

The dataset contains building-level information and hourly energy observations together with contextual information such as weather and metadata.

The project currently uses a selected subset of 12 buildings for development and validation.

The selected subset keeps the development workload manageable while retaining multiple buildings and different building characteristics.

---

# Raw Data Layout

The raw BDG2 files are stored under:

```text
data/raw/bdg2/
```

The main source files are:

```text
data/raw/bdg2/electricity_cleaned.csv
data/raw/bdg2/metadata.csv
data/raw/bdg2/weather.csv
```

These files form the source layer.

They are not modified directly by downstream application or model code.

All transformations should be performed through reproducible pipeline scripts so that the raw source remains an inspectable reference.

---

# Selected Buildings

The current development dataset contains 12 selected buildings:

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

The selected subset provides a manageable development scope while preserving multiple buildings and building characteristics.

---

# Initial Data Audit

The initial Phase 1 audit established the following:

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

The audit was used to establish that the selected data had the expected hourly structure and that generated temporal features were aligned with the underlying observations.

The presence of missing observations is treated as an explicit data-quality characteristic rather than assuming that the source is complete.

---

# Canonical Processed Dataset

The canonical Phase 1 feature dataset is:

```text
data/processed/phase1_features.parquet
```

Current size:

```text
Rows:    210,528
Columns: 44
```

This dataset contains the engineered features required by the Phase 1 ML experiments.

It is also used by the application API for historical consumption and prediction-context retrieval.

The Parquet representation is preferred for the processed analytical layer because it provides efficient columnar access while remaining easy to inspect and reproduce locally.

---

# Feature Dataset

The processed dataset combines several categories of information.

## Energy History

Historical electricity consumption is used to construct temporal features such as:

* lagged consumption
* recent consumption statistics
* rolling means
* rolling maximums
* other historical consumption context required by the feature pipeline

These features provide the model with information about recent building behaviour.

Historical features are particularly important because the prediction task is formulated as next-hour energy forecasting.

---

## Weather

Weather information provides environmental context for energy consumption.

Weather variables are incorporated into the feature dataset alongside building and temporal information.

Weather context is also part of the prediction-time request contract so that inference can reconstruct the same feature semantics used during model development.

---

## Building Metadata

Building-level metadata provides relatively static contextual information.

Examples include:

* site information
* primary use
* floor area
* timezone
* building characteristics

The application-facing building catalog contains additional metadata where available, including fields such as:

* latitude
* longitude
* year built
* number of floors
* occupants
* energy star score
* EUI
* site EUI
* heating type
* LEED level

---

## Calendar Features

Temporal features capture recurring consumption patterns.

These include calendar-derived information such as:

* hour
* weekday
* day
* month

Calendar features allow the model to represent systematic temporal consumption patterns.

---

## Degree-Hour Features

Heating and cooling degree-hour style features are included to represent temperature-related energy demand.

These provide additional context for weather-sensitive building consumption.

---

## Lag and Rolling Features

The forecasting feature set uses historical energy observations to derive lagged and rolling features.

The inference service reconstructs these features from the supplied historical observations rather than accepting a precomputed feature vector from the frontend.

This establishes a clear boundary:

```text
Historical observations
        ↓
Feature construction
        ↓
Model-ready feature vector
```

The same feature semantics are therefore preserved between training and serving.

---

# Forecast Target

The primary forecasting target is:

```text
target_next_hour_kwh
```

It represents the next-hour energy consumption associated with the current feature row.

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

The prediction problem is therefore a one-step-ahead hourly forecasting task.

---

# Temporal Alignment

Temporal alignment is a critical part of dataset construction.

The dataset is hourly.

Historical features must refer only to information available before the prediction timestamp.

Conceptually:

```text
t-168 ... t-2  t-1   t
   │              │    │
   │              │    └── Current prediction context
   │              └────── Recent history
   └───────────────────── Historical window
```

The inference service currently requires 168 consecutive hourly observations immediately preceding the prediction timestamp.

This corresponds to a seven-day historical window:

```text
168 hours = 7 days
```

The requirement is enforced at the ML-service boundary.

This prevents incomplete history from silently producing an invalid feature vector.

---

# Prediction-Time Data Contract

For the current inference path, a prediction requires:

```text
Target timestamp
+
Building metadata
+
Weather context
+
168 hourly historical observations
```

The application API obtains the relevant historical context from the processed dataset before sending the prediction request to the FastAPI model service.

The model service then:

1. validates the request
2. verifies the historical observations
3. reconstructs the required temporal features
4. combines them with building and weather context
5. produces the prediction
6. records the prediction for operational monitoring
7. returns model identity and serving information with the result

The prediction response includes:

```text
building_id
timestamp
predicted_energy_kwh
model_name
model_version
```

---

# Missing Data

The initial audit identified missing electricity observations and corresponding missing next-hour targets.

Missing values are therefore treated as an explicit data-quality concern.

The project does not assume that the source dataset is perfectly complete.

Downstream feature construction and inference logic must preserve the assumptions established during the Phase 1 pipeline.

In particular, the prediction-time history must contain sufficient valid observations for the required feature construction.

---

# Training / Inference Data Relationship

The same feature definitions are intended to be preserved between model development and model serving.

The conceptual relationship is:

```text
Processed Historical Data
          ↓
     Phase 1 Features
        ↙       ↘
   Training    Inference
      ↓           ↓
 Evaluation   Prediction
      ↓
    MLflow
```

The training pipeline generates the feature dataset used for model experiments.

The FastAPI inference service reconstructs the required feature representation from supplied historical context.

This reduces the risk of training-serving feature mismatch.

---

# Application Data Access

The processed feature dataset also serves as an application data source.

The Express application API currently uses the Parquet dataset for:

* historical consumption retrieval
* prediction-context retrieval
* application-level energy data access

The flow is:

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

It avoids introducing a database before the application has an operational requirement for one.

---

# Building Metadata for the Application

The application API uses an exported building metadata file:

```text
apps/api/src/data/buildings.json
```

The export is generated using:

```text
scripts/phase3_export_buildings.py
```

This provides the application layer with a stable representation of the selected buildings.

The export does not replace the original BDG2 source data.

The relationship is:

```text
BDG2 metadata
      ↓
Export script
      ↓
buildings.json
      ↓
Express API
      ↓
Next.js
```

---

# Data Ownership by Layer

The current data responsibilities are:

| Layer                | Data Responsibility                                                  |
| -------------------- | -------------------------------------------------------------------- |
| `data/raw/`          | Original source data                                                 |
| `data/processed/`    | Validated and engineered datasets                                    |
| `ml/`                | Data processing, feature engineering, training and ML pipeline logic |
| `models/`            | Local serialized model artifacts                                     |
| `apps/api/src/data/` | Application-facing building metadata                                 |
| Express API          | Historical data and prediction-context access                        |
| FastAPI              | Prediction-time validation and feature construction                  |
| MLflow               | Experiment, model-version and lifecycle metadata                     |
| Monitoring State     | Prediction and performance observations                              |
| Next.js              | Presentation of API responses                                        |

This separation prevents application code from becoming responsible for training-data transformations and prevents model lifecycle metadata from being mixed into the raw data layer.

---

# Data Flow Through the Current Platform

The complete current data path is:

```text
BDG2 Raw Data
      ↓
Phase 1 Validation
      ↓
Feature Engineering
      ↓
phase1_features.parquet
      ├───────────────────┐
      │                   │
      ▼                   ▼
ML Training          Application API
      │                   │
      ▼                   ▼
Evaluation           Historical Data
      │                   │
      ▼                   ▼
MLflow Tracking      Express API
      │                   │
      ▼                   │
Model Registry       │
      │                   │
      ▼                   │
FastAPI Model Service ────┘
      │
      ▼
Prediction
      │
      ▼
Monitoring
      │
      ├── Data Quality
      ├── Drift
      ├── Performance
      └── Service Health
      │
      ▼
Next.js Dashboard
```

The data layer therefore supports both:

```text
Analytical / ML path
```

and:

```text
Application / product path
```

without making either layer directly responsible for the other's implementation details.

---

# Current Storage Strategy

The project deliberately uses file-based storage during the early development phases.

Current data and artifact storage includes:

```text
Raw CSV
   ↓
Processed Parquet
   ↓
Model artifact / MLflow model
   ↓
JSON application metadata
```

The ML lifecycle additionally uses MLflow for:

```text
Training run
   ↓
Parameters
Metrics
Tags
Dataset / reproducibility metadata
   ↓
Registered model version
   ↓
Lifecycle status / aliases
```

Operational monitoring currently uses bounded in-memory state inside the model service.

This keeps the system:

* local
* reproducible
* inexpensive
* inspectable
* CPU-friendly
* suitable for a normal development laptop

---

# Why No Operational Database Yet?

A dedicated operational database has not yet been introduced.

The current requirements can be satisfied by:

* Parquet for historical analytical data
* JSON for the small application building catalog
* local model artifacts where required
* MLflow storage for experiment and model lifecycle state
* bounded in-memory state for current monitoring observations

A database can be justified later if the platform begins storing substantial operational state such as:

* prediction history
* monitoring measurements
* model metadata outside MLflow
* alerts
* user configuration
* retraining records
* production event history

The architecture therefore leaves room for a future database without prematurely adding one.

---

# Data Validation Philosophy

The project treats validation as a first-class stage.

The intended principle is:

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

Rather than:

```text
Raw Data
   ↓
Immediately Train Model
```

Important validation areas include:

* timestamp integrity
* hourly continuity
* duplicate keys
* missing values
* target alignment
* lag alignment
* building identity
* feature consistency
* inference history sufficiency
* invalid input values

The purpose is not merely to make training succeed.

The purpose is to establish explicit assumptions about the data before the data enters downstream ML and application systems.

---

# Data Reproducibility

Data-processing scripts are kept in the repository rather than relying on manual spreadsheet transformations.

Important scripts include:

```text
scripts/phase0_data_proof.py
scripts/phase1_build_features.py
scripts/phase3_export_buildings.py
```

These scripts make the major data transformations reproducible and inspectable.

The processed dataset can therefore be regenerated from the source layer rather than depending on undocumented manual operations.

---

# Dataset and Model Boundary

The processed feature dataset is not itself the model.

The distinction is:

```text
Data
 ↓
Features
 ↓
Training
 ↓
Evaluation
 ↓
Model Artifact
```

The model lifecycle is then handled separately:

```text
Model Artifact
      ↓
MLflow
      ↓
Registered Version
      ↓
Evaluation / Promotion
      ↓
Serving
```

This separation allows multiple model families to be evaluated against the same processed data without modifying the underlying data layer.

---

# Model Training Data

Phase 1 training uses:

```text
data/processed/phase1_features.parquet
```

The learned model families evaluated during the current lifecycle include:

```text
Ridge
Random Forest
HistGradientBoosting
```

Baseline strategies are evaluated separately from learned models.

The current baseline strategies include:

```text
Persistence
Previous Day
Previous Week
```

The persistence baseline predicts the next-hour value using the latest observed energy value.

Conceptually:

```text
latest observed energy
          ↓
next-hour prediction
```

The baseline is important because a learned model should demonstrate useful predictive value relative to a simple forecasting strategy rather than being evaluated only against other learned models.

---

# Baseline Data and Evaluation

The persistence baseline is treated as a first-class benchmark.

Current baseline results are stored in:

```text
reports/generated/phase1_baseline_results.csv
```

The baseline report contains the evaluated baseline strategies and their metrics.

The current persistence strategy is:

```text
pred_persistence
```

Display name:

```text
Persistence
```

Strategy:

```text
Use the latest observed energy value as the next-hour prediction.
```

The baseline is not considered a learned model and is therefore kept conceptually separate from the learned-model registry.

---

# Baseline-Aware Model Evaluation

Model evaluation distinguishes between:

```text
Learned model performance
```

and:

```text
Baseline performance
```

The purpose is to determine whether a learned candidate provides sufficient improvement to justify becoming a production model.

The promotion workflow therefore follows:

```text
Train learned models
        ↓
Evaluate learned models
        ↓
Select best evaluated learned candidate
        ↓
Compare against persistence baseline
        ↓
       ┌───────────────┐
       │               │
     Pass            Fail
       │               │
       ▼               ▼
Candidate          Reject candidate
eligible           for production
       │               │
       ▼               ▼
Promotion          Keep current
                   serving mode
```

The baseline comparison is a lifecycle decision and does not modify the underlying training dataset.

---

# MLflow and Data Reproducibility

MLflow provides experiment tracking and model registry capabilities around the existing data pipeline.

The underlying Phase 1 feature dataset remains unchanged.

MLflow records metadata associated with training runs, including relevant:

* parameters
* metrics
* tags
* model identity
* reproducibility information
* lifecycle state

The resulting relationship is:

```text
Dataset
   ↓
Training Configuration
   ↓
Training Run
   ↓
Metrics + Parameters + Reproducibility Metadata
   ↓
Registered Model Version
```

This provides a traceable connection between the data used for experimentation and the resulting model version.

---

# Data and Model Versioning Boundary

The project currently separates:

```text
Data version / dataset reference
```

from:

```text
Model version
```

A model version in MLflow does not imply that the underlying raw dataset itself has been independently versioned as a formal data registry.

Instead, training runs record relevant dataset and reproducibility metadata.

This distinction is intentional.

Future phases may introduce stronger dataset and feature versioning if the monitoring and retraining workflow requires it.

---

# Model Signature and Feature Contract

The MLflow-registered models have validated input signatures.

The signature establishes the expected feature representation at serving time.

The current model-service implementation uses the registered model signature to determine the model's expected feature columns rather than relying solely on manually maintained model-family assumptions.

Conceptually:

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

This reduces the risk of serving a feature vector whose structure differs from the model's training contract.

---

# Prediction Serving Data

The model service does not require the frontend to know how the model's internal feature vector is assembled.

Instead:

```text
Application API
      ↓
Building metadata
Weather context
Historical observations
      ↓
FastAPI
      ↓
Feature construction
      ↓
Registered model
      ↓
Prediction
```

This keeps feature engineering behind the model-service boundary.

The frontend therefore consumes a stable prediction API rather than directly depending on the internal feature implementation.

---

# Baseline Serving Mode

The system supports a safe fallback serving mode.

If no learned model qualifies for production, the model service can operate using the persistence baseline.

Conceptually:

```text
MLflow production alias available
             │
         ┌───┴───┐
        Yes      No
         │        │
         ▼        ▼
  Learned model  Persistence
    serving       serving
```

In baseline serving mode, the prediction is derived from the latest observed historical energy value.

The API still returns:

```text
model_name
model_version
```

so that the application can distinguish between:

```text
learned model serving
```

and:

```text
baseline serving
```

This prevents the application from presenting a baseline prediction as if it were a learned production model.

---

# Current Historical Forecasting Limitation

The source dataset ends on:

```text
2017-12-31
```

Therefore, the current application's forecast demonstration uses historical observations.

The data pipeline currently does not provide a live stream of present-day building measurements.

Consequently:

```text
Current system:
Historical data
      ↓
Inference
      ↓
Monitoring
      ↓
Dashboard
```

represents the current implementation.

The intended future operational architecture is:

```text
Live / Incoming Data
      ↓
Validation
      ↓
Feature Pipeline
      ↓
Inference
      ↓
Monitoring
      ↓
Retraining
```

This distinction is important when describing the project as a production-oriented ML platform.

The current system demonstrates the architecture and lifecycle mechanics locally; it is not yet a live building telemetry platform.

---

# Current Data Access Architecture

The current application uses the same processed historical dataset for multiple purposes:

```text
                    phase1_features.parquet
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
          Historical API          ML Context
                 │                     │
                 ▼                     ▼
             Dashboard              FastAPI
                                       │
                                       ▼
                                Feature Builder
                                       │
                                       ▼
                                     Model
```

This approach avoids unnecessary duplication of the historical dataset.

---

# Data Integrity and Service Boundaries

The project maintains explicit boundaries between data responsibilities.

The frontend should not:

* load raw BDG2 files
* construct ML feature vectors
* access model artifacts directly
* perform model lifecycle decisions

The Express API should not:

* train models
* modify model artifacts
* decide whether a candidate should be promoted

The FastAPI model service should not:

* serve as the application's historical data repository
* own frontend presentation logic
* bypass model validation

The ML pipeline should not:

* directly control the frontend
* depend on browser-specific behaviour
* modify raw source files

Monitoring should not:

* modify raw training data
* directly promote a model
* directly retrain a model
* replace the serving strategy without a lifecycle decision

This separation keeps the data flow understandable and testable.

---

# Reproducible Data Processing

The major transformations are represented as repository code.

Current important stages include:

```text
Phase 0
Data feasibility / proof
        ↓
Phase 1
Feature construction
        ↓
Processed Parquet
        ↓
Training / Evaluation
```

Application metadata export is handled separately:

```text
Processed / source metadata
        ↓
phase3_export_buildings.py
        ↓
apps/api/src/data/buildings.json
```

The separation allows the application catalog to remain stable without treating it as a replacement for the source dataset.

---

# Current Data Quality Monitoring

Phase 5 extends the existing data validation architecture with operational data-quality signals.

The monitoring layer considers conditions including:

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

The intended relationship is:

```text
Incoming Prediction Context
        ↓
Data-Quality Checks
        ↓
Monitoring Signal
        ↓
Prediction / Operational Analysis
```

Data-quality monitoring exists to distinguish model-performance problems from invalid or incomplete input data.

Critical data-quality problems should therefore be considered separately from genuine model degradation.

---

# Current Drift Data Architecture

Phase 5 introduces reference-based feature drift monitoring.

A reference feature profile is compared against current monitoring observations.

The conceptual flow is:

```text
Reference Feature Distribution
             +
Current Feature Observations
             ↓
        PSI Analysis
             ↓
      Drift Monitoring
```

The drift layer monitors relevant numerical prediction-context features such as:

* building characteristics
* calendar features
* historical energy features
* weather variables
* degree-hour features

The current drift thresholds are:

```text
Healthy:  PSI < 0.10
Warning:  0.10 <= PSI < 0.25
Critical: PSI >= 0.25
```

A minimum current sample count of 30 observations is required before a feature drift result is considered evaluable.

This prevents individual prediction requests from being treated as statistically meaningful distribution changes.

Drift is a supporting operational signal and does not independently trigger retraining.

---

# Monitoring Data

Monitoring data is operational data generated around the prediction lifecycle.

A monitoring prediction observation contains information such as:

```text
building_id
timestamp
prediction
persistence_baseline
model_name
model_version
serving_mode
```

When an actual outcome becomes available, the system can create a performance observation containing:

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

The distinction is:

```text
Prediction Event
      ↓
Prediction Observation
      ↓
Actual Outcome Available
      ↓
Performance Observation
```

A monitoring observation is therefore an operational prediction event.

It is not:

* one building
* one historical dataset row
* one training sample

The development dataset contains 12 selected buildings and 210,528 processed rows, while the monitoring state records prediction events generated by the running service.

---

# Monitoring Storage Strategy

The current monitoring implementation uses bounded in-memory state inside the model service.

The monitoring state is intentionally bounded to prevent unbounded memory growth.

This is suitable for the current local architecture.

The current system does not claim that monitoring observations are a durable production telemetry store.

A persistent operational monitoring datastore can be introduced in a later phase if the system requires:

* long-term telemetry retention
* multi-instance monitoring
* durable prediction history
* persistent alert history
* cross-process monitoring
* production-scale observability

---

# Prediction and Actual-Outcome Relationship

Model-performance monitoring requires both a prediction and the corresponding actual outcome.

The data flow is:

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

Without actual outcomes, the system can record prediction events but cannot calculate realized prediction error.

This distinction is important when interpreting monitoring observation counts.

---

# Performance Monitoring Data

Performance monitoring uses the prediction and actual outcome relationship to calculate:

* MAE
* RMSE
* NMAE
* persistence-baseline MAE
* persistence-baseline RMSE
* persistence-baseline NMAE

Performance can also be calculated per building.

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

The persistence baseline is calculated on the same observed outcomes so that model and baseline performance are directly comparable.

---

# Performance Degradation Data

The degradation layer evaluates rolling performance observations rather than individual predictions.

The current configuration is:

```text
Recent window size:          30 observations
Sustained windows required:  3
Relative degradation limit: 10%
Minimum observations:       90
```

The data requirement is therefore:

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

Fewer than 90 performance observations result in:

```text
insufficient_data
```

The detector distinguishes between:

```text
insufficient_data
healthy
degraded
```

A degraded state requires the sustained degradation condition to be met across all required windows.

This prevents short-lived changes from being treated as sufficient evidence for lifecycle action.

---

# Baseline-Aware Performance Monitoring

Performance monitoring retains the persistence baseline as an operational reference.

The comparison is:

```text
Served Model
      vs
Persistence Baseline
```

using the same actual outcomes.

This provides a consistent reference for interpreting model performance.

The monitoring layer therefore does not evaluate a learned model only against its own historical metrics.

It can also determine whether the served strategy is continuing to provide useful performance relative to the simple persistence benchmark.

---

# Data Quality and Retraining Boundary

Data quality is part of the evidence used to interpret model degradation.

The intended decision structure is:

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
        Evaluate model degradation
```

A model should not automatically become a retraining candidate when poor performance is primarily explained by invalid or incomplete incoming data.

---

# Drift and Retraining Boundary

Drift is also treated as supporting evidence rather than an automatic lifecycle trigger.

The intended relationship is:

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

Drift alone does not imply that the model should be retrained.

This prevents distribution changes that do not materially affect predictive performance from automatically initiating model lifecycle actions.

---

# Retraining Data

Future controlled retraining will require a clearly defined relationship between:

```text
Historical training data
```

and:

```text
New operational observations
```

The intended lifecycle is:

```text
Incoming observations
        ↓
Validation
        ↓
Storage
        ↓
Training dataset creation
        ↓
Candidate model
        ↓
Evaluation
        ↓
Baseline / production comparison
        ↓
Promotion decision
```

Retraining should not directly overwrite the production model.

A newly trained model is treated as a candidate until it passes the defined evaluation gates.

---

# Retraining Eligibility Data Contract

Phase 5 establishes the monitoring information required by the future retraining workflow.

The intended eligibility evidence is:

```text
Sufficient observations
        +
Sustained performance degradation
        +
Supporting drift evidence where relevant
        +
Learned model underperforms persistence baseline
        +
Data quality is not critical
        +
Service state is operational
        ↓
Retraining Eligible
```

The future eligibility state should contain:

* model identity
* model version
* serving mode
* sample count
* evaluation window
* current performance
* reference performance
* persistence-baseline performance
* drift state
* data-quality state
* service-health state
* degradation state
* reasons for eligibility

The current data layer provides the information required to construct this future state, but the actual retraining workflow belongs to Phase 6.

---

# Data Quality Principles

The project follows several core data principles.

## 1. Preserve raw data

Raw source files remain unchanged.

## 2. Make transformations reproducible

Important transformations are implemented as scripts.

## 3. Validate before modeling

Data assumptions are checked before training.

## 4. Preserve temporal causality

Features must not use information that would be unavailable at prediction time.

## 5. Separate training and serving responsibilities

Feature semantics must remain consistent without coupling the frontend to ML internals.

## 6. Treat baselines as first-class references

Learned models should be evaluated against meaningful simple forecasting strategies.

## 7. Keep data and model lifecycle concerns separate

The dataset is not the model, and a model version is not automatically a new dataset version.

## 8. Treat monitoring as operational data

Prediction observations and performance observations are separate from historical training data.

## 9. Avoid premature infrastructure

Operational databases and streaming infrastructure are introduced only when justified by actual system requirements.

---

# Current Data Limitations

The current data layer has several deliberate limitations:

* the source data is historical rather than live
* the source period ends on 2017-12-31
* the development scope contains only 12 selected buildings
* missing observations exist in the source data
* the current system does not have a production telemetry ingestion pipeline
* prediction history is maintained in bounded in-memory monitoring state rather than a dedicated persistent database
* formal automated dataset versioning is not yet implemented
* persistent operational monitoring storage is not yet implemented
* automatic retraining is not implemented
* live production data ingestion is not implemented

These limitations are explicit design boundaries rather than hidden assumptions.

---

# Current Data Status

The current data foundation is sufficient for:

* historical consumption visualization
* building-level exploration
* next-hour forecasting demonstrations
* feature-based ML experimentation
* learned-model evaluation
* baseline comparison
* MLflow model registration
* model-serving demonstrations
* local Docker-based reproducibility
* application-level prediction workflows
* prediction monitoring
* data-quality monitoring
* reference-based drift analysis
* outcome-based performance monitoring
* sustained degradation detection

It is not yet intended to represent:

* a live building telemetry platform
* a production-scale data warehouse
* a real-time streaming system
* a full BDG2-scale industrial deployment
* a durable production monitoring datastore
* an autonomous retraining system

---

# Data Architecture Summary

The current strategy deliberately prioritizes:

```text
Correctness
    +
Reproducibility
    +
Clear Data Boundaries
    +
Temporal Integrity
    +
Baseline Awareness
    +
Operational Observability
    +
Simple Local Infrastructure
```

The resulting architecture is:

```text
BDG2
  ↓
Raw Data
  ↓
Validation
  ↓
Feature Engineering
  ↓
Parquet
  ├──────────────────┐
  │                  │
  ▼                  ▼
ML Pipeline       Application
  │                  │
  ▼                  ▼
MLflow           Express API
  │                  │
  ▼                  │
Registry             │
  │                  │
  ▼                  │
FastAPI ─────────────┘
  │
  ▼
Prediction
  │
  ├── Data Quality
  ├── Drift
  ├── Performance
  └── Service Health
  │
  ▼
Next.js
```

The persistence baseline provides an additional forecasting path:

```text
Historical observations
          ↓
Persistence baseline
          ↓
FastAPI
          ↓
Next.js
```

when no learned model has been promoted for production serving.

The data layer is sufficient to support the completed Phase 1 ML pipeline, the Phase 3 application, the Phase 4 ML lifecycle and serving infrastructure, and the Phase 5 monitoring and observability layer.

Future phases can extend this foundation toward live operational ingestion, persistent telemetry, stronger dataset versioning, controlled retraining, and deployment without prematurely replacing the current simple and reproducible architecture.