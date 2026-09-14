# Machine Learning

## 1. Purpose

The machine learning layer provides the forecasting capability of the Building & Energy Intelligence Platform.

The primary ML task is:

> Predict the next hour's building electricity consumption (`target_next_hour_kwh`) using historical energy consumption, building metadata, weather information, and time-based features.

The ML system is designed around reproducibility, temporal correctness, leakage prevention, interpretable evaluation, and a clear distinction between production candidates and experimental models.

---

## 2. ML Problem Definition

### Task

Supervised regression for one-step-ahead electricity demand forecasting.

### Target

`target_next_hour_kwh`

The target represents the electricity consumption at the next hourly timestamp for a building.

Conceptually:

    X(t) → predict energy(t + 1 hour)

### Prediction unit

One observation corresponds to:

    building_id + timestamp

The model therefore operates on building-level hourly observations.

---

## 3. Input Feature Groups

The Phase 1 feature dataset contains the following feature groups.

### Building information

- `building_id`
- `site_id`
- `primary_use`
- `square_feet`
- `floor_area`
- `timezone`

These describe the building and its physical/contextual characteristics.

### Weather

- `air_temperature`
- `dew_temperature`
- `cloud_coverage`
- `wind_speed`
- `wind_direction`
- `sea_level_pressure`
- `precip_depth_1_hr`

Weather data is joined using:

    site_id + timestamp

### Calendar features

- `hour`
- `day_of_week`
- `month`
- `day_of_year`
- `is_weekend`

### Cyclical time features

- `hour_sin`
- `hour_cos`
- `day_of_year_sin`
- `day_of_year_cos`

These represent periodic temporal behavior without treating cyclic variables as purely linear quantities.

### Historical energy features

Lag features:

- `energy_lag_1h`
- `energy_lag_2h`
- `energy_lag_3h`
- `energy_lag_24h`
- `energy_lag_48h`
- `energy_lag_72h`
- `energy_lag_168h`

Rolling features:

- `energy_roll_mean_3h`
- `energy_roll_mean_6h`
- `energy_roll_mean_24h`
- `energy_roll_max_24h`
- `energy_roll_mean_168h`
- `energy_roll_max_168h`

### Degree-hour features

- `heating_degree_hour`
- `cooling_degree_hour`

These are derived from air temperature using the Phase 1 feature definition.

---

## 4. Leakage Prevention

Temporal leakage is treated as a first-class ML concern.

For a prediction at timestamp `t`, all energy-derived features must use observations strictly before `t`.

The model must never receive:

    energy(t)

when predicting:

    energy(t + 1)

Rolling features are therefore constructed after shifting the energy series so that the rolling window contains only historical observations.

The feature pipeline also verifies lag alignment against expected historical timestamps.

---

## 5. Temporal Dataset Splitting

Random train/test splitting is not used for the forecasting problem.

The dataset is divided chronologically into:

- training period
- validation period
- test period

This preserves the real forecasting direction:

    past → future

The test set represents future observations that were not available during model development.

---

## 6. Baseline Models

Simple forecasting baselines are required before evaluating more complex ML models.

### Persistence baseline

The next-hour prediction is the most recently observed energy value.

Conceptually:

    prediction(t + 1) = energy(t)

This baseline is especially important because building electricity consumption has strong temporal persistence.

### Previous-day baseline

Uses the corresponding observation from approximately 24 hours earlier.

    prediction(t + 1) = energy(t - 23h)

### Previous-week baseline

Uses the corresponding observation from approximately 168 hours earlier.

    prediction(t + 1) = energy(t - 167h)

The baselines provide a reference point for determining whether ML models actually add predictive value.

---

## 7. Candidate ML Models

Phase 1 evaluated three supervised regression models.

### Random Forest

A tree-based ensemble model capable of learning nonlinear relationships and interactions between:

- historical energy
- weather
- calendar variables
- building characteristics

### HistGradientBoosting

A gradient-boosted tree model evaluated as a second nonlinear challenger.

### Ridge Regression

A regularized linear model used as a simpler reference model.

The purpose of evaluating multiple model families is not to assume that the most complex model will win, but to establish an evidence-based benchmark.

---

## 8. Evaluation Metrics

The project uses multiple metrics because a single aggregate metric can hide important building-level behavior.

### MAE

Mean Absolute Error:

    MAE = mean(|y - ŷ|)

This represents the average absolute prediction error in kWh.

### RMSE

Root Mean Squared Error:

    RMSE = sqrt(mean((y - ŷ)^2))

RMSE penalizes larger errors more strongly than MAE.

### CVRMSE

Coefficient of Variation of RMSE:

    CVRMSE = RMSE / mean(actual)

This provides a scale-normalized measure of forecasting error.

### NMAE

Normalized Mean Absolute Error:

    NMAE = MAE / mean(actual)

This allows errors to be compared across buildings with different consumption scales.

### Macro building NMAE

NMAE is calculated independently for each building and then averaged across buildings.

This prevents buildings with very large energy consumption from completely dominating the evaluation.

---

## 9. Phase 1 Benchmark Results

The final Phase 1 test results were:

    Persistence
        MAE:  8.444619
        RMSE: 23.639729
        CVRMSE: 16.593072%
        NMAE: 0.059274
        Macro building NMAE: 0.094865

    Random Forest
        MAE: 10.873100
        RMSE: 24.717749
        CVRMSE: 17.364619%
        NMAE: 0.076385
        Macro building NMAE: 0.137032

    HistGradientBoosting
        MAE: 11.179845
        RMSE: 24.857629
        CVRMSE: 17.462887%
        NMAE: 0.078540
        Macro building NMAE: 0.373641

    Ridge
        MAE: 15.060576
        RMSE: 29.967921
        CVRMSE: 21.052950%
        NMAE: 0.105803
        Macro building NMAE: 4.231032

The previous-day and previous-week baselines performed worse than persistence.

---

## 10. Champion and Challenger

The benchmark produced an important result:

> The persistence baseline outperformed all evaluated ML models on the Phase 1 test set.

Therefore:

    Champion  = Persistence
    Challenger = Random Forest

Persistence is the current forecasting champion based on the available evidence.

Random Forest remains valuable as a challenger because it represents the first nonlinear ML model and provides a meaningful comparison against the simple baseline.

The project does not promote a model simply because it is an ML model.

---

## 11. Error Analysis

Phase 1 included building-level and temporal error analysis comparing Random Forest against persistence.

The analysis showed:

- Persistence was approximately 22.3% better than Random Forest in overall MAE.
- Random Forest performed better than persistence for one evaluated building.
- Random Forest performed better at selected hours, including 05:00, 06:00, and 21:00.
- Persistence remained stronger across the evaluated months.
- Persistence remained stronger for both weekday and weekend groups.

The results demonstrate that model performance is strongly dependent on building and temporal context.

The analysis should therefore be interpreted as evidence about this dataset and experiment rather than as a universal statement about building-energy forecasting.

---

## 12. Model Artifact

The Phase 1 Random Forest artifact is stored as:

    models/random_forest_phase1.joblib

The artifact contains:

- model name
- trained model
- feature column definition
- metadata

The artifact is consumed by the Phase 2 inference service.

The model artifact is treated as a versioned interface between model development and model serving.

---

## 13. Model Serving Contract

The serving layer must not recreate model training logic.

The inference service receives validated request data, reconstructs the required Phase 1 features, and passes the resulting feature frame to the stored model.

The serving boundary is independent of the internal model implementation.

Conceptually:

    API request
        ↓
    request validation
        ↓
    feature reconstruction
        ↓
    feature ordering
        ↓
    trained model
        ↓
    prediction response

This allows the model implementation to change without changing the external API contract.

---

## 14. Feature Parity

A critical requirement is that features generated during inference match the definitions used during training.

The inference service therefore reproduces the Phase 1 feature calculations for:

- calendar features
- cyclical features
- energy lags
- rolling statistics
- degree-hour features

The Phase 2 test suite includes a feature-parity test comparing inference-time feature construction against the Phase 1 feature builder.

This prevents silent training/serving skew.

---

## 15. Historical Context Requirement

A single current energy observation is not sufficient for the Phase 1 Random Forest model because the model depends on historical lag and rolling features.

The inference request therefore supplies:

    168 hourly observations

immediately preceding the prediction timestamp.

The service validates that:

- timestamps are unique
- timestamps are chronologically ordered
- observations are hourly
- the history is consecutive
- the history ends immediately before the prediction timestamp
- the required historical window is complete

This makes the API contract explicit instead of hiding missing historical context inside the service.

---

## 16. Missing Values

The Phase 1 dataset contains some missing energy and weather observations.

Missingness is therefore represented explicitly in the feature dataset and quality indicators are retained.

The serving layer validates request structure and numeric constraints before inference.

The current Phase 2 service does not introduce a new imputation strategy that was not part of the Phase 1 model pipeline.

Future ML phases may introduce more sophisticated missing-data handling when justified by experiments.

---

## 17. Reproducibility Principles

ML experiments should be reproducible through:

- fixed dataset definitions
- explicit feature definitions
- deterministic dataset splitting
- recorded model configuration
- saved model artifacts
- recorded evaluation metrics
- documented decisions
- version-controlled source code

Generated datasets, trained artifacts, and reports are not treated as ordinary source-code files in Git.

---

## 18. Current ML Architecture

The current ML flow is:

    BDG2 raw data
        ↓
    validation
        ↓
    feature engineering
        ↓
    temporal split
        ↓
    baseline evaluation
        ↓
    model training
        ↓
    model evaluation
        ↓
    error analysis
        ↓
    model artifact
        ↓
    FastAPI inference service

The React frontend, Node/Express application backend, monitoring, retraining, CI/CD, and deployment infrastructure are intentionally outside the current ML scope.

---

## 19. Current Status

### Completed

- Historical electricity forecasting problem defined
- BDG2 subset selected
- Feature dataset created
- Temporal leakage controls implemented
- Historical lag features implemented
- Rolling features implemented
- Weather features incorporated
- Calendar and cyclical features implemented
- Degree-hour features implemented
- Persistence baseline implemented
- Previous-day baseline implemented
- Previous-week baseline implemented
- Random Forest benchmarked
- HistGradientBoosting benchmarked
- Ridge benchmarked
- Building-level evaluation implemented
- Error analysis implemented
- Persistence established as champion
- Random Forest retained as challenger
- Random Forest artifact integrated into FastAPI inference service
- Inference feature parity tested
- Real HTTP prediction tested

### Not yet implemented

- Experiment tracking system
- Automated model registry
- Champion/challenger promotion workflow
- Production monitoring
- Data drift detection
- Prediction drift detection
- Automated retraining
- Model performance monitoring in production
- CI/CD
- Cloud deployment
- Advanced forecasting models

These are intentionally deferred to later phases.

---

## 20. ML Design Philosophy

The project follows an evidence-first ML approach:

    baseline → experiment → evaluate → compare → analyze → decide

A more sophisticated model is not automatically considered better.

The primary question is:

> Does the model provide measurable predictive value over a strong, simple baseline?

For the current Phase 1 dataset, the answer is no for the evaluated Random Forest, HistGradientBoosting, and Ridge models.

That result is retained as part of the project's ML evidence rather than hidden in favor of a more impressive-looking model.

The next ML iterations should therefore focus on understanding the forecasting problem and improving the experimental setup before adding unnecessary model complexity.