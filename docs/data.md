# Data

## Overview

The Building & Energy Intelligence Platform uses the Building Data Genome Project 2 (BDG2) as its initial data source.

The data pipeline is designed to transform raw building, electricity, weather, and metadata sources into a validated feature dataset that can be used consistently by both model training and inference.

The current pipeline is:

```text
Raw BDG2 Data
      ↓
Data Validation
      ↓
Cleaning / Alignment
      ↓
Feature Engineering
      ↓
Processed Feature Dataset
      ↓
ML Training / Evaluation
      ↓
ML Inference
````

---

# Source Dataset

The initial source is the Building Data Genome Project 2 (BDG2).

The dataset contains building-level information and hourly energy observations together with contextual information such as weather and metadata.

The project currently uses a selected subset of 12 buildings for development and validation.

---

# Raw Data Layout

The raw BDG2 files are stored under:

```text id="8b8q9x"
data/raw/bdg2/
```

The main source files are:

```text id="l9j7zs"
data/raw/bdg2/electricity_cleaned.csv
data/raw/bdg2/metadata.csv
data/raw/bdg2/weather.csv
```

These files remain the source layer.

They are not modified directly by downstream application or model code.

---

# Selected Buildings

The current development dataset contains 12 selected buildings:

```text id="h4y8az"
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

The audit was used to establish that the selected data had the expected hourly structure and that the generated temporal features were aligned with the underlying observations.

---

# Canonical Processed Dataset

The canonical Phase 1 feature dataset is:

```text id="j5yq3a"
data/processed/phase1_features.parquet
```

Current size:

```text id="xw9bq5"
Rows:    210,528
Columns: 44
```

This dataset contains the engineered features required by the Phase 1 ML experiments.

It is also currently used by the application API for historical consumption and prediction-context retrieval.

---

# Feature Dataset

The processed dataset combines several categories of information.

## Energy History

Historical electricity consumption is used to construct temporal features such as:

* lagged consumption
* recent consumption statistics
* rolling means
* rolling maximums

These features provide the model with information about recent building behavior.

---

## Weather

Weather information provides environmental context for energy consumption.

Weather variables are incorporated into the feature dataset alongside building and temporal information.

---

## Building Metadata

Building-level metadata provides relatively static contextual information.

Examples include:

* site information
* primary use
* floor area
* timezone

---

## Calendar Features

Temporal features capture recurring consumption patterns.

These include calendar-derived information such as:

* hour
* weekday
* day
* month

---

## Degree-Day Features

Heating and cooling degree-day style features are included to represent temperature-related energy demand.

These provide additional context for weather-sensitive building consumption.

---

## Forecast Target

The primary target is:

```text id="0y2w3x"
target_next_hour_kwh
```

It represents the next-hour energy consumption associated with the current feature row.

---

# Temporal Alignment

Temporal alignment is an important part of the dataset construction.

The dataset is hourly.

Historical features must refer only to information available before the prediction timestamp.

Conceptually:

```text id="n2x5b6"
t-168 ... t-2  t-1   t
   │              │    │
   │              │    └── Prediction target context
   │              └────── Recent history
   └───────────────────── Historical window
```

The inference service currently requires 168 consecutive hourly observations immediately preceding the prediction timestamp.

This requirement is enforced at the ML-service boundary.

---

# Missing Data

The initial audit identified missing electricity observations and corresponding missing next-hour targets.

Missing values are therefore treated as an explicit data-quality concern rather than silently assuming the source data is complete.

Downstream feature construction and inference logic must preserve the assumptions established by the Phase 1 pipeline.

---

# Training / Inference Data Relationship

The same feature definitions are intended to be preserved between model development and model serving.

The conceptual relationship is:

```text id="9c4vbn"
Processed Historical Data
          ↓
   Phase 1 Features
       ↙       ↘
 Training      Inference
    ↓             ↓
 Model        Prediction
```

The FastAPI inference service reconstructs the required feature representation from the supplied historical context.

This reduces the risk of training-serving feature mismatch.

---

# Application Data Access

During Phase 3, the processed feature dataset also became an application data source.

The Express application API currently uses the Parquet dataset for historical consumption and prediction-context retrieval.

The flow is:

```text id="v4n8qj"
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

```text id="9m4d1k"
apps/api/src/data/buildings.json
```

The export is generated using:

```text id="1zq8s6"
scripts/phase3_export_buildings.py
```

This provides the application layer with a stable representation of the selected buildings.

The export does not replace the original BDG2 source data.

---

# Data Ownership by Layer

The current data responsibilities are:

| Layer                | Data Responsibility                   |
| -------------------- | ------------------------------------- |
| `data/raw/`          | Original source data                  |
| `data/processed/`    | Validated and engineered datasets     |
| `ml/`                | Data processing and ML pipeline logic |
| `models/`            | Serialized ML artifacts               |
| `apps/api/src/data/` | Application-facing building metadata  |
| FastAPI              | Prediction-time feature construction  |
| Next.js              | Presentation of API responses         |

---

# Data Flow Through the Current Platform

The complete current data path is:

```text id="8w3m1e"
BDG2 Raw Data
      ↓
Phase 1 Validation
      ↓
Feature Engineering
      ↓
phase1_features.parquet
      ├───────────────┐
      │               │
      ▼               ▼
ML Training       Application API
      │               │
      ▼               ▼
Random Forest     Historical Data
      │               │
      ▼               │
FastAPI           Express API
      │               │
      └───────┬───────┘
              ▼
           Next.js
```

---

# Data Used for Prediction

For the current Random Forest inference path, prediction requires:

```text id="s0j8bz"
Target timestamp
+
Building metadata
+
Weather context
+
168 hourly historical observations
```

The application API obtains the relevant context from the processed dataset before sending the request to FastAPI.

The ML service then validates and transforms this information into the model's expected feature representation.

---

# Current Storage Strategy

The project deliberately uses file-based storage during the early development phases.

Current storage includes:

```text id="0s5a1b"
CSV
 ↓
Parquet
 ↓
Joblib model artifact
 ↓
JSON application metadata
```

This keeps the platform:

* local
* reproducible
* inexpensive
* easy to inspect
* CPU-friendly

---

# Why No Database Yet?

A dedicated operational database has not yet been introduced.

The current requirements can be satisfied by:

* Parquet for historical analytical data
* JSON for the small application building catalog
* joblib for the current model artifact

A database can be justified later if the platform begins storing operational state such as:

* prediction history
* monitoring measurements
* model metadata
* alerts
* user configuration
* retraining records

The architecture therefore leaves room for a future database without prematurely adding one.

---

# Data Validation Philosophy

The project treats validation as a first-class stage.

The intended principle is:

```text id="6v8bq2"
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

```text id="3d7h2m"
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

---

# Reproducibility

Data-processing scripts are kept in the repository rather than relying on manual spreadsheet transformations.

Important scripts include:

```text id="u4qk8m"
scripts/phase0_data_proof.py
scripts/phase1_build_features.py
scripts/phase3_export_buildings.py
```

This makes the major transformations reproducible and inspectable.

---

# Data and Model Boundary

The processed feature dataset is not itself the model.

The distinction is:

```text id="m5n3p7"
Data
 ↓
Features
 ↓
Training
 ↓
Model Artifact
```

The current Random Forest artifact is stored separately:

```text id="8e6q1z"
models/random_forest_phase1.joblib
```

This separation allows future models to be trained from the same processed dataset without modifying the underlying data layer.

---

# Historical Forecasting Limitation

The source dataset ends on:

```text id="4p7r2x"
2017-12-31
```

Therefore, the current application's forecast demonstration uses historical observations.

The data pipeline currently does not provide a live stream of present-day building measurements.

Consequently:

```text id="x1k8fd"
Current system:
Historical data → inference demonstration

Future production system:
Live data → feature pipeline → inference → monitoring
```

This distinction is important when describing the project as a production-oriented platform.

---

# Future Data Architecture

Later phases can extend the current data layer toward a more operational architecture.

The intended evolution is:

```text id="r8y4ks"
Historical / Incoming Data
          ↓
Data Validation
          ↓
Feature Pipeline
          ↓
Feature Storage
          ↓
Model Inference
          ↓
Prediction Storage
          ↓
Monitoring
```

Potential future additions include:

* automated ingestion
* data-quality monitoring
* feature versioning
* prediction storage
* drift detection
* operational databases
* retraining datasets

These are planned capabilities rather than current implementations.

---

# Data Architecture Summary

The current data architecture is:

```text id="6h2q1v"
                 ┌──────────────────────┐
                 │      BDG2 Raw Data   │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Validation + Feature │
                 │ Engineering          │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ phase1_features      │
                 │ .parquet             │
                 └───────┬───────┬──────┘
                         │       │
                    Training   Application
                         │       │
                         ▼       ▼
                    ML Model   Express API
                         │       │
                         ▼       │
                      FastAPI   │
                         │       │
                         └───┬───┘
                             ▼
                          Next.js
```

The current strategy deliberately prioritizes correctness, reproducibility, and clear data boundaries.

The data layer is now sufficient to support the completed Phase 1 ML pipeline and the Phase 3 end-to-end application.

Future phases will extend it toward operational data ingestion, monitoring, and automated ML lifecycle management.