# Phase 1 — Data Foundation and ML Baseline

## Objective

Phase 1 establishes the data and machine-learning foundation for the
Building & Energy Intelligence Platform.

The phase covers:

- source data acquisition
- dataset validation
- feature construction
- temporal feature engineering
- baseline forecasting
- machine-learning model training
- validation and test evaluation
- building-level evaluation
- error analysis
- selection of a champion and challenger model

The resulting dataset and model artifacts provide the foundation for the
Phase 2 inference service.

---

## Dataset

The project uses the BDG2 building energy dataset.

The selected source data contains:

- hourly electricity consumption
- building metadata
- weather observations

The working dataset contains 12 selected buildings.

The canonical processed feature dataset is:

`data/processed/phase1_features.parquet`

### Dataset size

- Rows: 210,528
- Buildings: 12
- Rows per building: 17,544
- Time range: 2016-01-01 00:00 through 2017-12-31 23:00
- Duplicate building/timestamp keys: 0
- Non-hourly rows: 0

---

## Data Validation

Phase 1 validates the temporal and structural integrity of the dataset.

Validation checks include:

- duplicate building/timestamp keys
- hourly timestamp continuity
- missing energy observations
- target availability
- lag correctness
- feature consistency

The final feature dataset contained:

- 18,169 missing energy observations
- 18,178 missing target observations

Weather availability varied by feature, with temperature-related variables
being substantially more complete than cloud coverage and precipitation.

---

## Feature Engineering

The feature pipeline produces calendar, temporal, historical-energy,
weather, and degree-day features.

### Calendar features

- hour
- day of week
- month
- day of year
- weekend indicator

### Cyclical features

- hour sine
- hour cosine
- day-of-year sine
- day-of-year cosine

### Historical energy features

Lags:

- 1 hour
- 2 hours
- 3 hours
- 24 hours
- 48 hours
- 72 hours
- 168 hours

Rolling features:

- 3-hour mean
- 6-hour mean
- 24-hour mean
- 24-hour maximum
- 168-hour mean
- 168-hour maximum

Rolling features are constructed using strictly past observations.

The implementation uses a one-step shift before rolling calculations so that
the current target interval cannot leak into the feature values.

### Weather features

- air temperature
- dew temperature
- cloud coverage
- wind speed
- wind direction
- sea-level pressure
- precipitation depth

### Degree-day features

- heating degree hour
- cooling degree hour

### Prediction target

The forecasting target is the next hourly energy consumption value:

`target_next_hour_kwh`

---

## Temporal Integrity

The feature pipeline was explicitly checked for temporal correctness.

Final audit results:

- 1-hour lag mismatches: 0
- 2-hour lag mismatches: 0
- 3-hour lag mismatches: 0
- 24-hour lag mismatches: 0
- 48-hour lag mismatches: 0
- 72-hour lag mismatches: 0
- 168-hour lag mismatches: 0

This provides evidence that the historical features align with their intended
timestamps.

---

## Models

Three machine-learning approaches were evaluated:

### Random Forest

A tree-based ensemble model used as the primary nonlinear ML candidate.

### HistGradientBoosting

A gradient-boosted tree model evaluated as an alternative nonlinear model.

### Ridge Regression

A linear model used as a simple ML reference.

The ML models were compared against forecasting baselines.

---

## Forecasting Baselines

Three simple temporal baselines were evaluated:

### Persistence

Uses the most recently observed energy value.

### Previous day

Uses the energy value from the same time on the previous day.

### Previous week

Uses the energy value from the same time one week earlier.

---

## Validation Results

### Validation NMAE

| Model | Overall NMAE | Macro Building NMAE |
|---|---:|---:|
| Random Forest | 0.083106 | 0.128728 |
| HistGradientBoosting | 0.085602 | 0.354963 |
| Ridge | 0.120572 | 4.421321 |

Random Forest was the strongest ML candidate on validation data.

---

## Test Results

| Model | MAE | RMSE | CVRMSE | NMAE | Macro Building NMAE |
|---|---:|---:|---:|---:|---:|
| Persistence | 8.444619 | 23.639729 | 16.593072% | 0.059274 | 0.094865 |
| Random Forest | 10.873100 | 24.717749 | 17.364619% | 0.076385 | 0.137032 |
| HistGradientBoosting | 11.179845 | 24.857629 | 17.462887% | 0.078540 | 0.373641 |
| Ridge | 15.060576 | 29.967921 | 21.052950% | 0.105803 | 4.231032 |
| Previous day | 16.720426 | 40.416804 | 28.317390% | 0.117149 | 0.198767 |
| Previous week | 20.289197 | 47.461508 | 33.232744% | 0.142066 | 0.227496 |

---

## Model Selection

The final evidence led to an important distinction between the best overall
forecasting method and the best machine-learning candidate.

### Champion

**Persistence**

Persistence achieved the lowest overall test error and the lowest macro
building NMAE.

Therefore, it is the current forecasting champion based on Phase 1 evidence.

### Challenger

**Random Forest**

Random Forest was the strongest machine-learning model among the tested ML
approaches, but it did not outperform persistence.

It is therefore retained as the ML challenger rather than being declared the
production champion.

This distinction prevents the project from claiming that a more complicated
ML model is automatically better than a simple baseline.

---

## Error Analysis

A dedicated error-analysis workflow compared Random Forest predictions
against persistence.

Overall test MAE:

- Random Forest: 10.860234
- Persistence: 8.444619

Persistence was approximately 22.3% better in overall MAE.

Random Forest performed better for one of the selected buildings
(`Bear_assembly_Jose`) and at several specific hours, including 05:00, 06:00,
and 21:00.

Persistence performed better across all evaluated months and both weekday and
weekend categories.

The analysis indicates substantial building-dependent and temporal variation
in forecasting difficulty.

These observations are treated as empirical patterns rather than causal
claims.

---

## Model Artifact

The Phase 1 Random Forest model artifact is stored as:

`models/random_forest_phase1.joblib`

The artifact contains the trained model together with the information required
by the Phase 2 inference service, including:

- model name
- model object
- feature columns
- metadata
- model version information

The artifact is consumed by the standalone FastAPI service implemented in
Phase 2.

---

## Phase 1 Outcome

Phase 1 successfully established the complete offline ML pipeline:

```text
Raw BDG2 data
    ↓
Validation
    ↓
Feature engineering
    ↓
Temporal feature verification
    ↓
Train / validation / test split
    ↓
Model training
    ↓
Baseline comparison
    ↓
Evaluation
    ↓
Error analysis
    ↓
Champion / challenger decision