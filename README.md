<div align="center">

# Building & Energy Intelligence Platform

### End-to-end ML forecasting and MLOps for building energy systems

<p><em>
A full-stack machine learning system for next-hour electricity forecasting, model evaluation, production inference,
monitoring, and controlled model lifecycle management.
</em></p>

<p>
<img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/scikit--learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white" alt="scikit-learn">
<img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=next.js&logoColor=white" alt="Next.js">
<img src="https://img.shields.io/badge/MLflow-0194E2?style=flat-square&logo=mlflow&logoColor=white" alt="MLflow">
<img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
</p>

<p>
<a href="https://github.com/Someshwar12/building-energy-intelligence">Repository</a>
&nbsp;&nbsp;·&nbsp;&nbsp;
64 tests passing
&nbsp;&nbsp;·&nbsp;&nbsp;
MIT License
</p>

</div>

---

## Overview

Building & Energy Intelligence Platform is an end-to-end ML/MLOps application built around **next-hour building electricity consumption forecasting**.

The project treats forecasting as a system rather than a single model. Historical building, weather, and temporal data are transformed into model-ready features, evaluated against explicit forecasting baselines, tracked through MLflow, exposed through a FastAPI inference service, and surfaced through a Next.js application.

The lifecycle continues beyond inference:

```text
Data
  ↓
Validation
  ↓
Feature Engineering
  ↓
Baseline Evaluation
  ↓
Model Training
  ↓
Evaluation
  ↓
MLflow Registry
  ↓
Promotion Gate
  ↓
Inference
  ↓
Monitoring
  ↓
Retraining Eligibility
  ↓
Candidate Retraining
  ↓
Promote / Reject
  ↓
Rollback
```

A central design decision is that **a trained model is not automatically a production model**. A learned candidate must demonstrate value over the persistence baseline before it can receive the production alias.

---

## Project Demo

A walkthrough of the Building & Energy Intelligence Platform, covering the application dashboard, energy analysis, forecasting, model lifecycle, monitoring, and anomaly detection.

**Demo video:** [Building & Energy Intelligence Platform — Full Walkthrough](./assets/building_video.mp4)

---

## System at a Glance

| Dimension | Implementation |
|---|---|
| Prediction task | Next-hour building electricity consumption |
| Dataset | BDG2 |
| Buildings | 12 |
| Historical period | 2016-01-01 → 2017-12-31 |
| Processed observations | 210,528 |
| Temporal context | 168 hourly observations |
| Learned models | Ridge, Random Forest, HistGradientBoosting |
| Primary baseline | Persistence |
| Model tracking | MLflow |
| Model registry | MLflow Model Registry |
| Inference | FastAPI |
| Frontend | Next.js / React |
| Deployment | Docker Compose |
| Monitoring | Data quality, drift, performance, service state |
| Lifecycle | Candidate → evaluation → promotion/rejection → rollback |
| Compute target | CPU-first, normal development laptop |

---

# Architecture

```text
                         ┌─────────────────────────────┐
                         │        Next.js Web           │
                         │            :3000             │
                         │ Buildings · Forecasts       │
                         │ Model Lab · Monitoring       │
                         └──────────────┬──────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │       Application API        │
                         │            :4000             │
                         │ Buildings · Consumption      │
                         │ Forecasts · Anomalies        │
                         └──────────────┬──────────────┘
                                        │
                                        ▼
                         ┌─────────────────────────────┐
                         │       FastAPI ML Service     │
                         │            :8000             │
                         │ Validation · Features        │
                         │ Inference · Monitoring       │
                         └──────────────┬──────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         │                             │
                         ▼                             ▼
              ┌─────────────────────┐       ┌─────────────────────┐
              │        MLflow       │       │   ML / Data Layer   │
              │        :5000        │       │ Features · Training │
              │ Tracking + Registry │       │ Evaluation · Lifecycle│
              └─────────────────────┘       └─────────────────────┘
```

### ML lifecycle architecture

```text
Historical Data
      │
      ▼
Data Validation
      │
      ▼
Feature Engineering
      │
      ├──────────────► Baseline Evaluation
      │
      ▼
Candidate Training
      │
      ▼
Experiment Tracking
      │
      ▼
Model Registry
      │
      ▼
Candidate Evaluation
      │
      ▼
┌───────────────────────────────┐
│        Promotion Gates        │
│                               │
│  1. Model evaluation          │
│  2. Persistence comparison    │
│  3. Production comparison     │
└───────────────┬───────────────┘
                │
          ┌─────┴─────┐
          ▼           ▼
       Reject       Promote
          │           │
          │           ▼
          │      @production
          │           │
          └─────┬─────┘
                ▼
            Inference
                │
                ▼
           Monitoring
                │
                ▼
     Retraining Eligibility
                │
                ▼
       Candidate Retraining
```

---

# Data and Feature Engineering

The ML pipeline is based on the BDG2 building-energy dataset.

### Source data

```text
data/raw/bdg2/
├── electricity_cleaned.csv
├── metadata.csv
└── weather.csv
```

The canonical processed dataset is:

```text
data/processed/phase1_features.parquet
```

It contains:

```text
210,528 rows
44 columns
12 buildings
2016-01-01 → 2017-12-31
```

### Feature groups

**Energy history**
- Lagged electricity consumption
- Rolling consumption statistics
- Recent temporal consumption history

**Weather**
- Air temperature
- Dew temperature
- Sea-level pressure
- Wind direction
- Wind speed
- Cloud coverage
- Precipitation depth

**Building metadata**
- Building ID
- Site ID
- Primary use
- Floor area / square feet

**Calendar**
- Hour
- Day
- Day of week
- Month

**Derived thermal features**
- Heating degree hours
- Cooling degree hours

The inference service reconstructs the required temporal features from a **168-hour history window**, keeping feature construction inside the ML service boundary rather than requiring clients to submit model-specific feature vectors.

---

# Machine Learning

## Prediction Objective

The system predicts:

```text
target_next_hour_kwh
```

for a given building and prediction timestamp.

The model combines:

```text
Historical energy
+ Weather
+ Building metadata
+ Calendar features
+ Lag features
+ Rolling features
+ Thermal features
        ↓
Next-hour electricity consumption
```

---

## Learned Models

Three model families were evaluated:

| Model | Role |
|---|---|
| Ridge | Regularized linear reference |
| Random Forest | Nonlinear ensemble |
| HistGradientBoosting | Gradient-boosted nonlinear model |

The system deliberately evaluates multiple model families rather than coupling the lifecycle to one algorithm.

---

## Evaluation Metrics

The project evaluates:

- **MAE** — Mean Absolute Error
- **RMSE** — Root Mean Squared Error
- **CVRMSE** — Coefficient of Variation of RMSE
- **NMAE** — Normalized Mean Absolute Error
- **Macro-building NMAE** — average normalized error across buildings

Macro-building NMAE is used for lifecycle decisions so that aggregate performance is not dominated by buildings with larger energy consumption.

### Original learned-model evaluation

| Model | Validation MAE | Validation RMSE | Validation CVRMSE | Validation NMAE | Validation Macro-Building NMAE | Test MAE | Test RMSE | Test NMAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Random Forest | 11.585128 | 28.264663 | 20.061556% | 0.082228 | 0.127556 | 10.830353 | 24.610103 | 0.076085 |
| HistGradientBoosting | 12.014662 | 29.071060 | 20.633917% | 0.085277 | 0.355616 | 11.015266 | 24.526046 | 0.077384 |
| Ridge | 16.439043 | 34.248344 | 24.308625% | 0.116680 | 4.065300 | 14.845004 | 29.860645 | 0.104289 |

---

# Baseline-First Model Governance

The project evaluates learned models against simple forecasting strategies:

```text
pred_persistence
pred_previous_day
pred_previous_week
```

The primary operational baseline is **persistence**:

```text
prediction = latest observed energy value
```

The original evaluation recorded:

```text
pred_persistence
NMAE = 0.0592740184411023
```

The production promotion metric is:

```text
validation_macro_building_nmae
```

The fundamental gate is:

```text
learned model
      │
      ▼
Does it beat persistence?
      │
   ┌──┴──┐
   │     │
  yes    no
   │     │
   ▼     ▼
continue reject
   │
   ▼
compare with production
   │
   ▼
promotion decision
```

This is one of the defining engineering properties of the system: **model complexity must demonstrate value over a simple baseline.**

---

# Model Registry and Experiment Tracking

MLflow provides:

- Experiment tracking
- Model registration
- Model versioning
- Model signatures
- Lifecycle metadata
- Promotion metadata
- Rejection metadata
- Rollback through model aliases

Registered model:

```text
building-energy-forecast
```

Production selection:

```text
@production
```

The distinction is intentional:

```text
Registered Model Version
          ≠
Production Model
```

A version can exist in the registry without being served.

---

# Inference Service

The FastAPI model service provides the runtime inference boundary.

```text
Prediction Request
        │
        ▼
Schema Validation
        │
        ▼
Serving Mode
    ┌───┴────┐
    │        │
Baseline  Learned
    │        │
    │        ▼
    │   Feature Construction
    │        │
    │        ▼
    │   Production Model
    │        │
    └────┬───┘
         ▼
     Prediction
         │
         ▼
 Non-negative output
         │
         ▼
 Prediction Response
```

The service supports MLflow-backed production serving.

Production configuration:

```text
MODEL_SOURCE=mlflow
MLFLOW_MODEL_NAME=building-energy-forecast
MLFLOW_MODEL_ALIAS=production
```

When no learned production model exists, the service can explicitly operate in **baseline serving mode** using persistence.

The serving state is observable through the monitoring and Model Lab interfaces.

---

# Monitoring

Monitoring is separated from training and deployment.

### Data quality

The system checks for:

- Schema validity
- Missingness
- Invalid values
- Duplicates
- Temporal gaps
- Frequency consistency

### Feature drift

The system compares:

- Reference distributions
- Recent distributions
- Drift diagnostics

### Model performance

When prediction/actual pairs are available:

- MAE
- RMSE
- NMAE
- Macro-building NMAE
- Global performance
- Per-building performance
- Persistence baseline comparison

### Service reliability

The system exposes:

- Readiness
- Serving mode
- Latency
- Operational state

Drift is treated as evidence, not as an automatic retraining command.

```text
Drift
  +
Performance evidence
  +
Data quality
  +
Service state
       ↓
Retraining Eligibility
```

---

# Controlled Retraining

The final lifecycle includes controlled production-data simulation and candidate retraining.

Generated datasets:

```text
data/interim/production/
├── normal_production.parquet
└── shifted_production.parquet
```

Simulation size:

```text
12 buildings × 168 hourly observations
= 2,016 rows
```

The shifted scenario introduces controlled changes to selected weather variables and target behavior.

Candidate retraining evaluates the same three learned model families.

### Phase 6 candidate results

| Version | Model | Candidate NMAE | Persistence NMAE | Lifecycle Decision |
|---|---|---:|---:|---|
| v4 | Ridge | 13.008031 | 0.219467 | Rejected |
| v5 | Random Forest | 9.466449 | 0.219467 | Rejected |
| v6 | HistGradientBoosting | 2.904410 | 0.219467 | Rejected |

All candidates failed the defined persistence-baseline gate.

Therefore the final registry state intentionally contains:

```text
@production
    ↓
No learned model
```

The platform continues with the persistence serving strategy.

This is not a missing feature or an artificially incomplete lifecycle. The system is behaving according to its defined production gate.

---

# Candidate Isolation and Rollback

Retraining never silently replaces production.

```text
                 ┌───────────────┐
                 │   Production  │
                 └───────┬───────┘
                         │
                         │ remains unchanged
                         │
                 ┌───────▼───────┐
                 │    Candidate  │
                 └───────┬───────┘
                         │
                   evaluation
                    ┌────┴────┐
                    ▼         ▼
                 Reject     Promote
                              │
                              ▼
                         @production
```

Rejected candidates remain in MLflow for auditability.

Rollback is implemented through the MLflow production alias and requires an existing learned production model.

If no learned production model exists, rollback is refused rather than simulated with fabricated state.

---

# Model Lifecycle Scripts

Important executable lifecycle components include:

```text
scripts/
├── phase1_build_features.py
├── phase1_train.py
├── simulate_production_data.py
├── retrain_candidate.py
├── promote_model.py
└── rollback_model.py
```

Lifecycle logic is also organized under:

```text
ml/lifecycle/
└── eligibility.py
```

This keeps lifecycle decisions explicit and testable rather than burying them inside application code.

---

# Web Application

The frontend exposes the ML system through dedicated application views.

| Route | Purpose |
|---|---|
| `/` | Application landing page |
| `/buildings` | Building overview |
| `/buildings/[buildingId]` | Building-level view |
| `/consumption` | Consumption analysis |
| `/forecasts` | Forecasting |
| `/anomalies` | Anomaly analysis |
| `/model-lab` | Model and lifecycle inspection |
| `/monitoring` | Operational and ML monitoring |

The **Model Lab** exposes registry and lifecycle information, while **Monitoring** exposes operational, data-quality, drift, and performance information.

---

# Repository Structure

```text
building-energy-intelligence/
│
├── apps/
│   ├── web/                    # Next.js frontend
│   ├── api/                    # Application API
│   └── model_service/          # FastAPI ML service
│
├── ml/
│   ├── ingestion/              # Data ingestion
│   ├── validation/             # Data validation
│   ├── features/               # Feature engineering
│   ├── training/               # Model training
│   ├── evaluation/             # Model evaluation
│   ├── monitoring/             # ML monitoring
│   ├── lifecycle/              # Retraining/lifecycle logic
│   └── artifacts/              # ML artifacts
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data/
│
├── configs/                    # Configuration
├── scripts/                    # Reproducible project/lifecycle scripts
├── docker/                     # Dockerfiles
├── .github/workflows/          # CI workflows
│
├── docs/
│   ├── architecture.md
│   ├── data.md
│   ├── decision_log.md
│   ├── ml.md
│   ├── phases.md
│   └── phase6_completion.md
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── reference/
│
├── models/                     # Local model artifacts
├── reports/                    # Generated reports
├── notebooks/                  # Exploratory notebooks
│
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── LICENSE
└── README.md
```

---

# Technology Stack

| Layer | Technologies |
|---|---|
| Data / ML | Python 3.11, NumPy, Pandas, scikit-learn, PyArrow |
| ML lifecycle | MLflow |
| Inference | FastAPI, Uvicorn |
| Application API | TypeScript |
| Frontend | Next.js, React, TypeScript, Recharts |
| Testing | Pytest |
| Code quality | Ruff, TypeScript type checking |
| Infrastructure | Docker, Docker Compose |
| Version control | Git, GitHub |

The project is intentionally CPU-first and designed to run on a normal development laptop. It does not depend on GPUs, large language models, transformers, or autonomous agents.

---

# Running Locally

## Prerequisites

- Python 3.11
- Node.js 22
- npm
- Docker Desktop
- Git

## Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Run the complete stack

```powershell
docker compose up --build
```

After the images have been built:

```powershell
docker compose up
```

The local services are:

| Service | Port | Purpose |
|---|---:|---|
| Web | `3000` | Next.js application |
| API | `4000` | Application API |
| Model Service | `8000` | FastAPI inference service |
| MLflow | `5000` | Tracking and model registry |

Open the relevant `localhost` address in your browser after the stack is running.

---

# Verification

The final implementation was verified across the Python ML/lifecycle layer and the TypeScript application layer.

```text
Python test suite       64 passed, 2 warnings
Ruff                    All checks passed
API typecheck           Passed
Web lint                Passed
Web production build    Passed
```

The test suite covers data validation, feature logic, model behavior, inference, monitoring/lifecycle components, production simulation, and retraining eligibility.

---

# Engineering Decisions

Several decisions define the system's behavior:

### Baselines are first-class evaluation artifacts

A learned model is not evaluated only against other learned models. Persistence remains an explicit operational reference.

### Production is an explicit state

A registered model version does not become production until the promotion process assigns `@production`.

### Retraining is controlled

Drift alone does not trigger automatic retraining. Retraining eligibility considers multiple signals.

### Candidates are isolated

A newly trained model cannot silently replace the serving model.

### Rejection is a valid lifecycle outcome

If a candidate fails the production gate, it remains rejected and production state is preserved.

### Rollback is state-aware

Rollback is available through the registry alias when a learned production model exists and is refused when there is nothing valid to roll back from.

### Production state is honest

The system does not fabricate a successful promotion simply to demonstrate the existence of a promotion mechanism.

---

# Limitations and Scope

The current implementation is a complete portfolio-scale ML/MLOps system, but its scope is explicit.

It does not claim:

- Live external building telemetry
- Autonomous production retraining
- Automatic model promotion
- Guaranteed learned-model superiority
- Real-world energy savings
- Commercial-scale deployment
- Industrial production operation

The Phase 6 production datasets are controlled simulations used to exercise the lifecycle.

The persistence strategy remains the current operational serving path because the tested learned candidates did not satisfy the promotion gate.

---

# Documentation

The repository contains detailed living documentation:

| Document | Coverage |
|---|---|
| `docs/architecture.md` | System architecture and component boundaries |
| `docs/data.md` | Dataset, validation, feature engineering, and data storage |
| `docs/ml.md` | ML methodology, evaluation, serving, monitoring, and lifecycle |
| `docs/phases.md` | Final implementation history from Phase 0 through Phase 6 |
| `docs/decision_log.md` | Architectural and engineering decisions |
| `docs/phase6_completion.md` | Final lifecycle implementation and verification |

---

# Project Status

## Implementation Complete

The defined implementation scope is complete through **Phase 6**.

Completed:

- Data feasibility and validation
- Feature engineering
- Baseline forecasting
- Learned model training
- Multi-metric evaluation
- MLflow experiment tracking
- MLflow model registry
- Model signatures
- FastAPI inference
- Next.js application
- Docker containerization
- Model Lab
- Monitoring
- Anomaly detection
- Automated testing
- CI verification
- Retraining eligibility
- Controlled production-data simulation
- Candidate retraining
- Promotion gate
- Candidate rejection
- Rollback mechanism
- Final technical documentation

There is no Phase 7 in the defined project scope.

---

# License

This project is licensed under the MIT License.

See [`LICENSE`](LICENSE) for the full license text.

---

<div align="center">

<strong>Building & Energy Intelligence Platform</strong>

<br>

<sub>Machine Learning · MLOps · Data Science · Software Engineering</sub>

<br><br>

<a href="https://github.com/Someshwar12/building-energy-intelligence">GitHub Repository</a>

</div>
