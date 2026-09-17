# Phase 5 Completion — Testability, CI & Observability

## 1. Phase Objective

Phase 5 extended the Building & Energy Intelligence Platform from a functioning ML application into a testable and observable ML system.

The objective was to establish:

- automated software and ML testing
- API and service integration coverage
- continuous integration checks
- data-quality monitoring
- feature drift detection
- prediction and model-performance monitoring
- sustained model-degradation detection
- service-health observability
- a controlled entry contract for future retraining

Phase 5 does **not** implement automatic retraining. Retraining remains a Phase 6 concern.

---

## 2. Phase Scope

### Included

- Python unit and integration testing
- FastAPI inference testing
- Node.js API verification
- frontend verification
- CI validation with GitHub Actions
- monitoring state and metrics
- data-quality signals
- reference-based feature drift detection
- prediction outcome tracking
- model-vs-baseline performance comparison
- rolling performance analysis
- sustained degradation detection
- monitoring dashboard integration
- service-health signals
- Phase 6 retraining eligibility contract

### Explicitly Excluded

- automatic retraining
- automatic model promotion
- production deployment
- autonomous remediation
- automatic replacement of the serving model

The system can identify evidence that may justify retraining, but the retraining workflow itself belongs to Phase 6.

---

## 3. Testing Foundation

Phase 5 established automated verification across the main layers of the platform.

### Python / ML layer

The test suite covers:

- data validation
- feature generation
- lag and rolling-window behavior
- missing-history handling
- feature schema compatibility
- prediction behavior
- prediction validity
- baseline behavior
- model identity
- FastAPI inference contracts
- monitoring behavior
- drift calculations
- performance calculations
- degradation detection

Final local result:

```text
47 passed, 2 warnings
````

The test suite completed successfully with no failing tests.

### API layer

The Node.js API was verified through:

```text
npm run typecheck
npm run build
```

Both completed successfully.

The API does not currently define an `npm run lint` script. Therefore, API linting is not reported as a Phase 5 check and no new lint system was introduced solely for phase closure.

### Frontend layer

The web application was verified through:

```text
npm run lint
npm run build
```

Both completed successfully.

The production build generated the expected application routes:

```text
/
/_not-found
/anomalies
/buildings
/buildings/[buildingId]
/consumption
/forecasts
/model-lab
/monitoring
```

---

## 4. CI

Continuous integration was extended to automatically verify important repository changes.

The CI validation includes the core checks required to prevent broken changes from entering the repository.

### Python

* pytest
* Ruff

### Node.js API

* TypeScript type checking
* production build

### Web application

* ESLint
* production build

The CI workflow was intentionally kept focused on fast, deterministic checks.

Long-running operations such as complete historical retraining, large-scale evaluation, full Docker rebuilds, and extensive monitoring analysis are not required for every repository change.

---

## 5. ML Lifecycle Observability

Phase 5 added observability around the model-serving lifecycle established in Phase 4.

The system can expose:

* registered model versions
* model family
* MLflow run identity
* validation status
* lifecycle status
* promotion metadata
* baseline information
* model metrics
* model parameters
* model tags
* candidate/production state

The Model Lab interface makes the registered model lifecycle visible without requiring direct inspection of the MLflow backend.

The currently registered learned models remain:

* Ridge
* Random Forest
* HistGradientBoosting

The learned models were evaluated against the persistence baseline during the earlier lifecycle work. The persistence baseline remains the serving fallback because the learned models did not satisfy the baseline guard on the selected validation criterion.

Phase 5 monitoring therefore preserves the distinction between:

1. the model registered in MLflow,
2. the model actually being served,
3. the persistence baseline,
4. the observed prediction performance.

---

## 6. Monitoring Architecture

Phase 5 introduced an in-process monitoring layer in the model service.

Monitoring records are maintained separately from the historical training dataset.

The monitoring state tracks prediction events and, when actual outcomes become available, prediction-performance observations.

The monitoring state is bounded to prevent unbounded in-memory growth.

```text
Prediction Request
       │
       ├──► Prediction
       │
       ├──► Monitoring State
       │       ├── Prediction record
       │       ├── Data-quality signals
       │       ├── Drift signals
       │       └── Service-health signals
       │
       └──► Later actual outcome
                  │
                  └──► Performance observation
```

Monitoring is therefore an operational layer over the serving system rather than a replacement for the historical training dataset.

---

## 7. Prediction Monitoring

Each prediction can be associated with:

* building ID
* prediction timestamp
* predicted energy
* persistence baseline
* model name
* model version
* serving mode

The monitoring layer therefore preserves the identity of the prediction that was actually served.

This is important because model performance must be evaluated against the model and serving mode that produced each prediction.

### Monitoring observations

A monitoring observation represents a prediction/inference event recorded by the monitoring state.

It does **not** represent:

* one building
* one historical dataset row
* one training sample

The development dataset contains 12 selected buildings and 210,528 processed rows. Monitoring observation counts are independent of that historical dataset size.

---

## 8. Data-Quality Monitoring

Phase 5 established monitoring signals for common data-quality failures.

The intended monitored conditions include:

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

The purpose is to distinguish a genuine model-quality problem from a problem caused by invalid or incomplete input data.

This distinction becomes important for future retraining decisions.

A model should not be considered a retraining candidate solely because its performance appears poor when the incoming data itself is invalid.

---

## 9. Feature Drift Monitoring

Phase 5 introduced reference-based drift detection using Population Stability Index (PSI).

The drift implementation:

* loads a reference feature profile
* extracts monitoring features from prediction requests
* compares current values against reference distributions
* calculates PSI
* maps PSI to health states
* handles insufficient samples
* handles unavailable reference data
* ignores non-finite observations

Configured thresholds:

```text
Healthy:  PSI < 0.10
Warning:  0.10 <= PSI < 0.25
Critical: PSI >= 0.25
```

A minimum current sample count is required before drift is evaluated:

```text
MIN_DRIFT_SAMPLE_COUNT = 30
```

This prevents individual observations from being interpreted as statistically meaningful distribution drift.

### Important distinction

Drift is treated as a **supporting signal**, not as an automatic retraining trigger.

A feature distribution can change without the model becoming operationally worse.

---

## 10. Model Performance Monitoring

Phase 5 added outcome-based performance tracking.

A prediction becomes a performance observation when the corresponding actual energy value is available.

For each outcome, the system records:

* prediction
* actual value
* persistence baseline
* absolute error
* squared error
* building ID
* timestamp
* model identity
* serving mode

The system calculates:

* MAE
* RMSE
* NMAE
* persistence-baseline MAE
* persistence-baseline RMSE
* persistence-baseline NMAE

Performance can also be calculated per building.

This allows both global and building-level performance analysis.

---

## 11. Baseline-Aware Performance

The persistence baseline is retained as a reference throughout monitoring.

The persistence strategy is:

> Use the latest observed energy value as the next-hour prediction.

Performance monitoring therefore compares:

```text
Served model
      vs
Persistence baseline
```

on the same observed outcomes.

This avoids evaluating model degradation in isolation.

A model may have a nonzero error while still providing useful predictive value, whereas a model that consistently performs worse than a simple baseline requires a different operational interpretation.

---

## 12. Sustained Degradation Detection

Phase 5 added explicit sustained-degradation logic.

The system does not classify a model as degraded because of one poor prediction or one poor rolling window.

Configured defaults are:

```text
Recent window size:          30 observations
Sustained windows required:  3
Relative degradation limit: 10%
Minimum observations:       90
```

Therefore:

```text
30 observations
    ↓
one performance window

30 observations
    ↓
second performance window

30 observations
    ↓
third performance window

90 observations total
    ↓
sustained-degradation evaluation
```

The degradation detector requires all three evaluated windows to satisfy the degradation condition before returning a degraded state.

With fewer than 90 performance observations, the system returns:

```text
insufficient_data
```

This deliberately reduces the chance of triggering retraining from short-lived noise.

---

## 13. Degradation State Semantics

The degradation evaluation distinguishes between:

```text
insufficient_data
healthy
degraded
```

The intended interpretation is:

### insufficient_data

There are not enough outcome observations to establish the required sustained performance window.

### healthy

There is sufficient data, but the sustained degradation condition has not been met.

### degraded

There is sufficient data and all required sustained windows satisfy the degradation condition.

This state is an evidence signal and does not itself retrain or replace a model.

---

## 14. Service Health

Phase 5 also added operational service observability.

The monitoring architecture considers:

* request availability
* prediction errors
* request latency
* health state
* readiness state
* dependency/service availability

The model service continues to expose health and readiness endpoints independently from the prediction endpoint.

This separates:

```text
Service is running
```

from:

```text
Service is ready to serve predictions
```

and from:

```text
Model performance is healthy
```

These are different operational conditions and are therefore monitored separately.

---

## 15. Monitoring Dashboard

The Monitoring page exposes the operational state of the ML system through the web application.

The dashboard integrates the monitoring information required for Phase 5, including:

* service state
* prediction observations
* model/serving information
* data-quality signals
* drift signals
* performance information where outcomes exist
* baseline comparison
* degradation state
* recent monitoring information

The dashboard is intended as an operational observability surface rather than a training notebook replacement.

---

## 16. Docker Runtime Verification

The Docker Compose environment contains four services:

```text
web
api
model-service
mlflow
```

The model service was rebuilt after the monitoring/inference fixes and the stack was started successfully.

Final runtime state verified:

```text
web             Running
api             Running
model-service   Running
mlflow          Healthy
```

The monitoring and prediction paths were verified through the running application.

The model-service container is therefore running the Phase 5 monitoring/inference implementation rather than an outdated pre-fix image.

---

## 17. Runtime Reliability Fix

During Phase 5 integration testing, an actual runtime failure was identified in monitoring instrumentation.

Optional weather fields could contain `None`, while monitoring feature extraction attempted to convert those values directly to floating-point numbers.

This caused prediction requests to fail with a server-side error.

The monitoring feature extraction was corrected so optional weather features are only included when values are present.

This was an important Phase 5 result: observability code must not become a new failure point for the prediction path.

After the correction, the complete Python test suite passed and the model-service image was rebuilt.

---

## 18. Monitoring and Prediction Separation

A core Phase 5 engineering principle is that monitoring must not break prediction.

The intended request path is:

```text
Request
  ↓
Validation
  ↓
Prediction
  ↓
Monitoring instrumentation
```

Monitoring failures should be handled independently from the core model-serving responsibility wherever possible.

This protects the primary application capability:

```text
building data → forecast
```

while still allowing operational telemetry to be collected.

---

## 19. Phase 5 Safety Boundaries

Phase 5 intentionally does not allow monitoring signals to directly modify the production model.

The system does not automatically:

* retrain
* promote
* demote
* replace
* delete
* roll back
* deploy

a model based on monitoring output.

This prevents noisy drift or short-lived performance changes from causing uncontrolled model lifecycle actions.

---

## 20. Phase 6 Retraining Eligibility Contract

Phase 5 establishes the evidence required before future retraining logic can be introduced.

A future retraining workflow should require sufficient evidence across multiple signals.

The intended conditions are:

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
Retraining eligible
```

Drift alone must not trigger retraining.

Poor performance caused by critical data-quality problems must not automatically trigger retraining.

Short-lived degradation must not trigger retraining.

The resulting state should contain enough context to explain why retraining became eligible.

Expected future eligibility information includes:

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

The actual retraining workflow is deferred to Phase 6.

---

## 21. Engineering Decisions

### Decision 1 — Keep persistence as the operational baseline

The persistence baseline remains available even when learned models are registered in MLflow.

Reason:

The baseline provides a simple reference point for both model promotion and ongoing performance monitoring.

### Decision 2 — Require sustained degradation

Performance degradation must persist across multiple windows before being classified as degraded.

Reason:

Single-window anomalies can be caused by temporary conditions and should not automatically initiate lifecycle actions.

### Decision 3 — Require minimum sample counts

Drift and degradation calculations require minimum observation counts.

Reason:

Very small samples can produce unstable or misleading monitoring signals.

### Decision 4 — Keep drift separate from retraining

Drift is supporting evidence rather than an automatic retraining trigger.

Reason:

Distribution change does not necessarily imply predictive-performance failure.

### Decision 5 — Keep monitoring in the serving layer

Monitoring is attached to the model-service prediction lifecycle.

Reason:

This preserves the identity of the model, version, serving mode, and input associated with each prediction.

### Decision 6 — Do not introduce automatic retraining in Phase 5

Reason:

Phase 5 establishes trustworthy signals first. Automated lifecycle actions belong to the next phase and should consume validated monitoring evidence.

---

## 22. Final Verification Status

### Automated verification

```text
Python pytest                  PASS
Python Ruff                    PASS
API TypeScript typecheck       PASS
API production build           PASS
Web ESLint                     PASS
Web production build           PASS
```

### Runtime verification

```text
Docker Compose                 PASS
MLflow                         HEALTHY
Model service                  RUNNING
API                            RUNNING
Web application                RUNNING
Prediction path                VERIFIED
Monitoring page                VERIFIED
```

### Phase 5 implementation

```text
Testing                        COMPLETE
CI foundation                  COMPLETE
Data-quality monitoring        COMPLETE
Drift monitoring               COMPLETE
Prediction monitoring          COMPLETE
Performance monitoring         COMPLETE
Degradation detection          COMPLETE
Service health                 COMPLETE
Monitoring UI                  COMPLETE
Retraining eligibility        ESTABLISHED
Automatic retraining           DEFERRED TO PHASE 6
```

---

## 23. Phase 5 Completion Criteria

Phase 5 is considered complete when:

* automated tests pass
* static Python checks pass
* API type checking passes
* API build passes
* frontend lint passes
* frontend build passes
* Docker runtime is operational
* prediction remains functional
* monitoring is accessible
* data-quality signals exist
* drift signals exist
* performance tracking exists
* baseline comparison exists
* sustained degradation detection exists
* monitoring does not break prediction
* Phase 6 retraining eligibility requirements are explicitly defined
* documentation reflects the implemented architecture
* the Phase 5 completion record is committed to the repository

---

## 24. Phase 5 → Phase 6 Boundary

At the end of Phase 5, the platform has the foundation required to answer:

```text
Is the service healthy?
Is the incoming data healthy?
Has the input distribution changed?
How is the served model performing?
How does it compare with persistence?
Is degradation sustained?
Is there enough evidence to consider retraining?
```

Phase 6 begins only after these signals can be consumed by a controlled retraining workflow.

The Phase 6 system should therefore build on the monitoring state rather than bypassing it.

---

## 25. Final Phase State

Phase 5 transforms the platform from a system that can **make predictions** into a system that can also **measure and explain the operational condition of those predictions**.

The resulting lifecycle is:

```text
Historical Data
      ↓
Validation
      ↓
Feature Engineering
      ↓
Model Training
      ↓
Evaluation
      ↓
MLflow Registry
      ↓
Model Serving / Baseline Serving
      ↓
Prediction
      ↓
Monitoring
 ┌────┼───────────────┐
 ↓    ↓               ↓
Data  Drift      Performance
Quality           Monitoring
 └────┼───────────────┘
      ↓
Sustained Degradation Detection
      ↓
Retraining Eligibility
      ↓
             PHASE 6
```

Phase 5 does not automatically cross the final boundary.

It provides the evidence and controls required to make that transition safely in Phase 6.