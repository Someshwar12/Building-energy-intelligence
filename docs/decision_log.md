# Decision Log

This document records important engineering, data, machine-learning, and
architecture decisions made during development of the Building & Energy
Intelligence Platform.

The purpose of this document is to preserve not only what was decided, but
also why the decision was made.

---

## Decision 001 — Use BDG2 as the Initial Dataset

**Decision:** Use the BDG2 building energy dataset as the initial development
dataset.

**Reason:**

BDG2 provides hourly building electricity consumption together with building
metadata and weather observations.

This provides the required ingredients for developing an end-to-end building
energy forecasting and ML lifecycle.

The dataset also supports evaluation across multiple buildings rather than
testing only a single time series.

---

## Decision 002 — Start With a Controlled Multi-Building Subset

**Decision:** Start development with 12 selected buildings rather than the
entire available dataset.

**Reason:**

The initial goal is to establish a complete and reproducible pipeline.

A controlled subset keeps local processing and experimentation practical while
still allowing the system to evaluate performance across multiple buildings.

The architecture should remain capable of expanding to more buildings later.

---

## Decision 003 — Use Hourly Next-Hour Forecasting

**Decision:** Define the initial forecasting problem as predicting the next
hour's building electricity consumption.

**Reason:**

Hourly forecasting provides a concrete operational ML problem while keeping
the initial system computationally manageable.

For an observation at time `t`, the target is:

```text
energy(t + 1)
````

---

## Decision 004 — Treat the Problem as a Temporal Forecasting Problem

**Decision:** Preserve chronological ordering when creating train, validation,
and test datasets.

**Reason:**

Energy forecasting is inherently temporal.

A random row-level split could allow future observations to appear in training
while earlier observations are used for evaluation, producing an unrealistic
estimate of production performance.

Temporal splitting better represents the way the model will operate after
deployment.

---

## Decision 005 — Prevent Temporal Data Leakage

**Decision:** Historical and rolling features must use only information that
would have been available before the prediction timestamp.

**Reason:**

The model predicts a future energy value.

Using information from the target interval would allow the model to indirectly
see the answer during feature construction and would invalidate the evaluation.

Rolling energy features therefore use strictly past observations.

---

## Decision 006 — Shift Before Rolling

**Decision:** Shift the energy series by one hour before calculating rolling
features.

**Implementation concept:**

```text
past_energy = energy.shift(1)
```

**Reason:**

This guarantees that rolling statistics for a prediction interval do not
include the energy value from that same interval.

This rule is important both for offline training and online inference.

---

## Decision 007 — Include Historical Energy Lags

**Decision:** Use historical energy lags at 1h, 2h, 3h, 24h, 48h, 72h, and
168h.

**Reason:**

Building energy consumption has strong short-term, daily, and weekly temporal
patterns.

These lag features provide the model with multiple historical reference
points.

---

## Decision 008 — Include Rolling Energy Statistics

**Decision:** Include rolling energy means and maximums over short and long
windows.

**Reason:**

Individual lag values describe specific historical points, while rolling
statistics describe recent consumption behavior.

The selected windows capture short-term, daily, and weekly patterns.

Current rolling features include:

* 3-hour mean
* 6-hour mean
* 24-hour mean
* 24-hour maximum
* 168-hour mean
* 168-hour maximum

All rolling features use strictly past observations.

---

## Decision 009 — Include Weather Information

**Decision:** Include available weather observations as model features.

**Reason:**

Building energy demand can vary with environmental conditions.

The dataset provides weather variables that can be aligned with building
energy observations by site and timestamp.

The initial weather features include:

* air temperature
* dew temperature
* cloud coverage
* wind speed
* wind direction
* sea-level pressure
* precipitation depth

Missing weather values are preserved rather than silently fabricated.

---

## Decision 010 — Add Degree-Day Features

**Decision:** Derive heating and cooling degree-hour features using an 18°C
base temperature.

**Reason:**

Degree-day style features provide a compact representation of heating and
cooling demand relative to a reference temperature.

The features are:

```text
heating_degree_hour
cooling_degree_hour
```

---

## Decision 011 — Include Calendar and Cyclical Features

**Decision:** Include calendar and cyclical representations of time.

**Reason:**

Building energy consumption can exhibit systematic hourly, weekly, and
seasonal patterns.

The feature set therefore includes:

* hour
* day of week
* month
* day of year
* weekend indicator
* hour sine/cosine
* day-of-year sine/cosine

---

## Decision 012 — Evaluate Simple Forecasting Baselines

**Decision:** Compare machine-learning models against simple forecasting
baselines.

The implemented baselines are:

* persistence
* previous day
* previous week

**Reason:**

A more complex ML model should demonstrate measurable value over simple
forecasting strategies.

This prevents model complexity from being treated as evidence of model
quality.

---

## Decision 013 — Evaluate Multiple ML Model Families

**Decision:** Evaluate Random Forest, HistGradientBoosting, and Ridge
Regression.

**Reason:**

The initial benchmark should include nonlinear tree-based models and a linear
reference model.

This provides a useful comparison between different model assumptions without
introducing unnecessary computational complexity.

---

## Decision 014 — Use Multiple Evaluation Metrics

**Decision:** Evaluate models using MAE, RMSE, CVRMSE, NMAE, and macro building
NMAE.

**Reason:**

A single metric does not fully describe forecasting performance.

MAE provides an interpretable absolute error measure.

RMSE emphasizes larger errors.

CVRMSE provides normalized error relative to the energy scale.

NMAE provides normalized absolute error.

Macro building NMAE prevents larger buildings from completely dominating the
evaluation.

---

## Decision 015 — Evaluate Performance Per Building

**Decision:** Include building-level evaluation in addition to aggregate
metrics.

**Reason:**

Different buildings can have very different energy consumption scales and
behavior.

An aggregate metric can hide poor performance on smaller buildings.

Building-level evaluation provides a more balanced view of model behavior.

---

## Decision 016 — Persistence Is the Current Forecasting Champion

**Decision:** Select persistence as the current forecasting champion.

**Reason:**

Persistence achieved the strongest final test performance among the evaluated
forecasting approaches.

Final test performance included:

```text
MAE:                 8.444619
NMAE:                0.059274
Macro Building NMAE: 0.094865
```

The project therefore does not automatically select the most complex ML model
as the production champion.

---

## Decision 017 — Random Forest Is the Current ML Challenger

**Decision:** Retain Random Forest as the strongest ML challenger.

**Reason:**

Random Forest was the strongest machine-learning model evaluated during Phase
1.

However, it did not outperform persistence on the final test set.

Therefore it remains an ML challenger rather than being declared the overall
forecasting champion.

---

## Decision 018 — Preserve the Champion/Challenger Distinction

**Decision:** Track the best overall forecasting method separately from the
best ML candidate.

**Reason:**

This creates an evidence-based model lifecycle.

A model should not be promoted simply because it is newer, more complex, or
machine-learning based.

Future models must demonstrate improvement against the current champion before
being considered for promotion.

---

## Decision 019 — Keep the Random Forest Artifact for Phase 2

**Decision:** Use the trained Random Forest artifact as the initial ML model
served by the Phase 2 inference service.

**Reason:**

Although persistence is the current forecasting champion, the project also
needs a genuine ML model to establish the complete model-serving lifecycle.

Random Forest is the strongest ML candidate from Phase 1 and therefore provides
a suitable first model artifact for the inference service.

The artifact is:

```text
models/random_forest_phase1.joblib
```

---

## Decision 020 — Separate Training and Inference

**Decision:** Implement model inference as a standalone FastAPI service.

**Reason:**

The application should not directly depend on the internals of the training
pipeline or the scikit-learn implementation.

A service boundary allows the ML system to evolve independently from the
future application backend and frontend.

---

## Decision 021 — Separate the ML Service From the Application Backend

**Decision:** Use:

```text
apps/model_service/
```

for the ML inference service and reserve:

```text
apps/api/
```

for the future Node/Express application backend.

**Reason:**

The two components have different responsibilities.

The ML service handles model inference.

The application backend will eventually handle application-level business
logic, persistence, authentication, orchestration, and user-facing APIs.

Keeping them separate avoids unnecessary coupling.

---

## Decision 022 — Load the Model Once at Startup

**Decision:** Load the model artifact during FastAPI application startup.

**Reason:**

Loading the model for every prediction would introduce unnecessary disk I/O and
latency.

A service-lifetime model instance provides a simpler and more efficient
inference path.

---

## Decision 023 — Validate the Model Artifact

**Decision:** The model loader validates that the loaded artifact contains the
expected structure.

Expected components include:

* model name
* model object
* feature columns
* metadata

**Reason:**

A file existing on disk does not guarantee that it is a valid model artifact.

Explicit validation prevents malformed artifacts from being treated as usable
models.

---

## Decision 024 — Normalize Model-Loading Failures

**Decision:** Normalize low-level model artifact loading failures into a
predictable application-level error.

**Reason:**

Serialization libraries can raise different low-level exceptions for missing,
corrupt, or incompatible artifacts.

The rest of the application should not depend on those implementation-specific
exceptions.

---

## Decision 025 — Expose Health and Readiness Separately

**Decision:** Provide separate `/health` and `/ready` endpoints.

**Reason:**

A running process is not necessarily a usable ML service.

`/health` confirms that the service process is alive.

`/ready` confirms that the required model has successfully loaded and the
service is ready to perform inference.

This distinction becomes important for future deployment and orchestration.

---

## Decision 026 — Use Explicit Pydantic API Schemas

**Decision:** Use Pydantic models for prediction requests and responses.

**Reason:**

The API needs an explicit contract for:

* building metadata
* weather values
* timestamps
* historical energy
* prediction responses

Validation at the API boundary prevents malformed data from unnecessarily
reaching model inference.

---

## Decision 027 — Require 168 Hours of Historical Context

**Decision:** Require 168 historical hourly observations for prediction
requests.

**Reason:**

The current Random Forest feature set contains lag and rolling features that
extend to 168 hours.

A prediction request containing only the current observation would not contain
enough information to reconstruct the training feature set.

---

## Decision 028 — Validate Historical Timestamp Structure

**Decision:** Historical observations must have:

* unique timestamps
* chronological ordering
* consecutive hourly intervals
* exactly 168 observations immediately preceding the prediction timestamp

**Reason:**

Correct historical alignment is essential for lag and rolling features.

Incorrect timestamp structure could produce valid-looking but incorrect model
features.

---

## Decision 029 — Verify Training/Serving Feature Parity

**Decision:** Maintain a dedicated regression test comparing API feature
construction against the Phase 1 feature builder.

**Reason:**

Training-serving skew is a major ML engineering failure mode.

The model can appear to work while producing incorrect predictions if the
inference service constructs features differently from training.

The parity test protects this contract.

---

## Decision 030 — Test the Real Model Through the HTTP Boundary

**Decision:** Include an automated test that sends a valid request through the
actual `/predict` endpoint using the real Phase 1 Random Forest artifact.

**Reason:**

Unit tests using fake models verify individual components but do not prove that
the actual deployed inference path works.

The real-model endpoint test verifies:

```text
HTTP Request
    ↓
FastAPI
    ↓
Validation
    ↓
Feature Construction
    ↓
Real Model
    ↓
Prediction
    ↓
HTTP Response
```

---

## Decision 031 — CPU-First Development

**Decision:** Keep the initial system runnable on a normal development laptop
without requiring a GPU.

**Reason:**

The project should remain reproducible, accessible, and practical during
development, testing, portfolio demonstration, and local execution.

---

## Decision 032 — Delay Infrastructure Until the Core System Is Stable

**Decision:** Do not introduce Docker, CI/CD, MLflow, monitoring, drift
detection, or automated retraining before the core data and inference
contracts are established.

**Reason:**

Infrastructure should support a functioning system rather than obscure or
complicate an unstable foundation.

The project therefore develops the system incrementally.

---

## Decision 033 — Use Git Checkpoints at Meaningful Milestones

**Decision:** Commit and push changes at meaningful engineering checkpoints
rather than after every small modification.

**Reason:**

The Git history should communicate meaningful project milestones while
avoiding excessive commit noise.

Phase-level checkpoints also provide recovery points during development.

---

## Decision 034 — Keep Generated Artifacts Out of Git

**Decision:** Generated datasets, model outputs, reports, caches, virtual
environments, and generated package metadata should not be committed unless
they are intentionally versioned project artifacts.

**Reason:**

Generated files can be large, reproducible, or environment-specific.

Keeping them out of the normal source-control path keeps the repository clean
and focused on source code, configuration, documentation, and intentionally
tracked artifacts.

---

## Decision 035 — Build the Platform Incrementally

**Decision:** Complete and verify each major phase before introducing the next
major architectural layer.

**Reason:**

The project is intended to demonstrate an actual ML engineering lifecycle,
not simply a collection of technologies.

Each phase should therefore leave the repository in a working and testable
state before the next layer is introduced.

The current progression is:

```text
Phase 0
Data Proof
    ↓
Phase 1
Data + ML Baseline
    ↓
Phase 2
ML Inference Service
    ↓
Phase 3
Application Backend
    ↓
Phase 4
Web Dashboard
    ↓
Phase 5+
Infrastructure, Lifecycle, Monitoring,
Retraining, and Deployment