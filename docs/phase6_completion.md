# Phase 6 — Complete ML Lifecycle & Project Completion

## Status

**Complete**

Phase 6 is the final implementation phase of the Building & Energy Intelligence Platform.

There is no subsequent implementation phase in this project.

Phase 6 completes the machine-learning lifecycle, controlled retraining workflow, model evaluation and promotion logic, rollback capability, lifecycle observability, and final project documentation.

The project ends with a fully tested local ML/MLOps platform in which the persistence baseline remains the active serving strategy because the Phase 6 retrained candidates did not outperform it under the defined evaluation gate.

This outcome is intentional and is preserved as part of the project's lifecycle evidence.

---

# 1. Phase Objective

The objective of Phase 6 was to complete the ML lifecycle around the system established during Phases 1–5.

Before Phase 6, the system already contained:

```text
Data
  ↓
Validation
  ↓
Feature Engineering
  ↓
Training
  ↓
MLflow
  ↓
Model Registry
  ↓
FastAPI
  ↓
React
  ↓
Monitoring
  ↓
Drift / Performance Detection
````

Phase 6 extended this into a controlled lifecycle:

```text
New Production-like Data
        ↓
Validation
        ↓
Monitoring
        ↓
Possible Degradation
        ↓
Retraining Eligibility
        ↓
Candidate Training
        ↓
Experiment Tracking
        ↓
Candidate Evaluation
        ↓
Production / Baseline Comparison
        ↓
Promotion Decision
       / \
      /   \
  Reject  Promote
    ↓        ↓
Production  @production
unchanged      ↓
            Inference
               ↓
           Monitoring
```

The implementation deliberately separates monitoring, retraining, evaluation, promotion, and rollback.

---

# 2. Final System Architecture

The final application architecture is:

```text
                         ┌──────────────────────┐
                         │     Next.js / React  │
                         │      Web App         │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   Node.js / Express  │
                         │   Application API    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │    ML Inference      │
                         └──────────┬───────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
              Persistence                    MLflow
               Baseline                       Server
                                                   │
                                                   ▼
                                           Model Registry
                                                   │
                                                   ▼
                                          Candidate Models
                                                   │
                                                   ▼
                                              Evaluation
                                                   │
                                                   ▼
                                           Promotion Gate
                                             /        \
                                            /          \
                                         Reject       Promote
                                           │             │
                                           │             ▼
                                           │       @production
                                           │             │
                                           └─────────────┤
                                                         ▼
                                                     Inference
                                                         │
                                                         ▼
                                                     Monitoring
                                                ┌────────┼────────┐
                                                ▼        ▼        ▼
                                              Drift  Performance Health
                                                │        │        │
                                                └────────┼────────┘
                                                         ▼
                                               Retraining Eligibility
                                                         │
                                                         ▼
                                               Candidate Retraining
```

The system remains intentionally local and CPU-first.

No Kubernetes, cloud orchestration, distributed streaming infrastructure, GPU infrastructure, or large-model infrastructure was introduced.

---

# 3. Retraining Eligibility

Phase 6 introduced an explicit retraining eligibility contract in:

```text
ml/lifecycle/eligibility.py
```

The eligibility layer converts monitoring evidence into a structured lifecycle decision.

The eligibility decision considers:

* completed performance observations
* minimum observation requirements
* sustained performance degradation
* comparison between the learned model and persistence
* feature drift state
* data-quality state
* model-service state

The resulting state distinguishes:

```text
retraining_eligible
```

from:

```text
not_eligible
```

Retraining eligibility does not itself train a model.

Its responsibility is to determine whether sufficient evidence exists to begin a controlled candidate-training process.

---

# 4. Drift Does Not Automatically Trigger Retraining

A central Phase 6 design decision is that feature drift does not automatically cause model retraining.

The lifecycle distinguishes between:

```text
Feature Drift
```

and:

```text
Predictive Performance Degradation
```

Drift is supporting evidence.

Performance degradation is required as part of the retraining eligibility decision.

This prevents the system from retraining merely because incoming feature distributions changed.

A distribution can change without making the existing model operationally unacceptable.

The lifecycle therefore follows:

```text
Drift
  ↓
Supporting Evidence
  ↓
Performance Analysis
  ↓
Sustained Degradation
  ↓
Retraining Eligibility
```

rather than:

```text
Drift
  ↓
Automatic Retraining
```

---

# 5. Production-Data Simulation

The current project uses the historical Building Data Genome Project 2 dataset rather than a live building telemetry stream.

Because of this, Phase 6 introduced a deterministic production-data simulation to demonstrate operational lifecycle behaviour without falsely claiming that the application receives live production telemetry.

The simulation script is:

```text
scripts/simulate_production_data.py
```

It uses the processed Phase 1 feature dataset as its source.

The selected production-like window contains:

```text
2016 rows
12 buildings
168 observations per building
```

Two scenarios are generated.

## Normal Scenario

The normal scenario represents production-like observations without a meaningful distribution shift.

Output:

```text
data/interim/production/normal_production.parquet
```

## Shifted Scenario

The shifted scenario introduces a controlled distribution change.

The simulation applies deterministic changes to selected environmental variables and the target energy values.

The shifted scenario produced:

```text
air_temperature_mean: 13.647
dew_temperature_mean: 9.137
wind_speed_mean: 2.269
target_next_hour_kwh_mean: 143.491
```

Output:

```text
data/interim/production/shifted_production.parquet
```

The simulation uses a fixed seed so the lifecycle demonstration is reproducible.

The simulated production data is explicitly a demonstration mechanism and is not presented as real telemetry.

---

# 6. Candidate Retraining

Candidate retraining was implemented in:

```text
scripts/retrain_candidate.py
```

The retraining workflow operates independently of the production-serving state.

The process is:

```text
Simulated Production Data
        ↓
Feature Preparation
        ↓
Chronological Train / Evaluation Split
        ↓
Candidate Model Training
        ↓
MLflow Experiment
        ↓
MLflow Model Registry
```

The candidate models are:

```text
Ridge
Random Forest
HistGradientBoosting
```

The retraining experiment is:

```text
building-energy-retraining
```

The registered model is:

```text
building-energy-forecast
```

Candidate training does not assign the `@production` alias.

This guarantees that training a candidate cannot directly replace the serving model.

---

# 7. Candidate Versions Generated

The Phase 6 retraining process generated:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

Each candidate was recorded in MLflow with lifecycle and experiment metadata.

The candidates were therefore available for independent evaluation before any production decision.

---

# 8. Candidate Evaluation

Candidate evaluation was implemented through:

```text
scripts/promote_model.py
```

Despite the script name, the workflow does not automatically promote a model.

It first evaluates registered retraining candidates against the simulated production evaluation window.

The evaluation uses normalized mean absolute error:

```text
NMAE
```

and compares each candidate with the persistence baseline.

The Phase 6 shifted-production evaluation produced:

| Version | Model                | Candidate NMAE | Persistence NMAE |
| ------: | -------------------- | -------------: | ---------------: |
|      v4 | Ridge                |      13.008031 |         0.219467 |
|      v5 | Random Forest        |       9.466449 |         0.219467 |
|      v6 | HistGradientBoosting |       2.904410 |         0.219467 |

These numbers belong specifically to the deterministic Phase 6 shifted-production evaluation.

They are not live production metrics.

---

# 9. Persistence Baseline Remains First-Class

The persistence strategy is intentionally treated as a first-class benchmark throughout the project.

It is used during:

```text
Evaluation
Promotion
Serving
Performance Monitoring
Retraining Eligibility
```

The principle is:

```text
A learned model should not be deployed merely
because it is better than the other learned models.
```

The relevant question is:

```text
Does the learned candidate actually justify
replacing the existing persistence strategy?
```

This prevents the lifecycle from assuming that a machine-learning model must always replace a simpler operational strategy.

---

# 10. Phase 6 Promotion Result

The Phase 6 evaluation produced the following decision:

```text
v4 Ridge
    ↓
Rejected

v5 Random Forest
    ↓
Rejected

v6 HistGradientBoosting
    ↓
Rejected
```

The reason was the same for all three candidates:

```text
The candidate did not beat the persistence baseline
under the Phase 6 evaluation criterion.
```

The evaluation therefore did not justify promotion of a learned model.

The system did not artificially promote the strongest learned candidate merely because it was the strongest among the learned candidates.

---

# 11. Why No Learned Model Was Promoted

The absence of a learned production model is an intentional result of the evaluation policy.

The Phase 6 lifecycle encountered:

```text
Candidate Training
       ↓
Candidate Evaluation
       ↓
Persistence Comparison
       ↓
Baseline Guard
       ↓
FAIL
       ↓
Reject Candidate
       ↓
Keep Existing Serving Strategy
```

The resulting registry state contains no learned model with the:

```text
@production
```

alias.

This is not an implementation failure.

It is the outcome produced by the project's explicit promotion rule.

The system is designed to allow the evaluation process to conclude:

```text
No learned candidate currently justifies production deployment.
```

---

# 12. Final Serving Strategy

Because no learned model passed the promotion guard, the model service continues using the persistence baseline.

The final serving state is:

```text
model_name    = persistence
model_version = baseline
serving_mode  = baseline
```

In baseline mode, the next-hour prediction uses the most recent observed energy value from the supplied historical context.

Conceptually:

```text
Latest observed energy
        ↓
Persistence prediction
        ↓
Next-hour forecast
```

This allows the application to remain operational without pretending that an unqualified learned model is production-ready.

---

# 13. Candidate vs Production

Phase 6 establishes an explicit distinction between candidate and production models.

A candidate is:

```text
trained
tracked
registered
evaluated
```

but is not necessarily production.

Production is only established through the controlled promotion process.

The lifecycle is therefore:

```text
Candidate
   ↓
Evaluation
   ↓
Promotion Gate
   ↓
Explicit Approval
   ↓
@production
```

Training alone cannot change production.

---

# 14. Promotion Control

The promotion workflow supports explicit approval through:

```text
--approve-version
```

A candidate must satisfy the evaluation gates before it can be promoted.

The promotion mechanism therefore separates:

```text
Candidate Evaluation
```

from:

```text
Production Promotion
```

This prevents accidental deployment of a newly trained model.

---

# 15. Rejection Metadata

Rejected models remain in MLflow rather than being deleted.

Their lifecycle metadata records information such as:

* model family
* validation status
* lifecycle state
* evaluation metrics
* persistence comparison
* promotion metric
* baseline guard result
* rejection reason

This preserves the model-development history and makes the reason for the lifecycle decision inspectable.

---

# 16. Rollback

Rollback capability was implemented in:

```text
scripts/rollback_model.py
```

The rollback mechanism operates through the MLflow production alias.

The intended workflow is:

```text
Existing @production
        ↓
Select known registered version
        ↓
Validate target
        ↓
Restore @production alias
        ↓
Record rollback metadata
```

Rollback validates:

* that a production model exists
* that the requested target version exists
* that the target version is ready
* that the target is not already production

The rollback process records metadata including:

* rollback timestamp
* previous production version
* restored version
* rollback reason
* rollback status

During Phase 6 verification, rollback was intentionally tested while no learned production alias existed.

The result was:

```text
No learned production model currently exists.
Rollback cannot be demonstrated until a production alias exists.
```

This is correct safety behaviour.

The system does not fabricate a production deployment solely to create an artificial rollback demonstration.

---

# 17. Model Lab

The existing Model Lab was extended through the completed ML lifecycle work and serves as the application's model-lifecycle observability surface.

It exposes information including:

* registered model versions
* MLflow runs
* model families
* lifecycle metadata
* validation state
* promotion metadata
* rejection metadata
* persistence baseline
* production state
* model metrics
* model parameters

The Model Lab distinguishes between:

```text
Model Lifecycle
```

and:

```text
Runtime Monitoring
```

so that registry and experiment information is not confused with live operational behaviour.

---

# 18. Monitoring

The Monitoring surface remains responsible for operational observability.

It provides visibility into:

* service health
* readiness
* active serving mode
* model identity
* prediction reliability
* latency
* feature drift
* data quality
* performance
* recorded errors

The monitoring system remains separate from retraining.

Monitoring provides evidence.

Retraining is a controlled lifecycle operation that consumes that evidence.

---

# 19. End-to-End Lifecycle Demonstration

The completed project can demonstrate the following sequence:

```text
1. Start the application.

2. Inspect a building and its historical consumption.

3. Generate a next-hour forecast.

4. Inspect anomaly information.

5. Open Model Lab and inspect the model lifecycle.

6. Observe that the current serving strategy is the
   persistence baseline.

7. Generate normal production-like observations.

8. Generate shifted production-like observations.

9. Inspect drift and monitoring behaviour.

10. Evaluate prediction performance.

11. Determine whether retraining evidence exists.

12. Train candidate models from the simulated
    production-like data.

13. Track the candidate experiments in MLflow.

14. Register the candidate model versions.

15. Evaluate the candidates.

16. Compare the candidates with persistence.

17. Apply the promotion guard.

18. Reject candidates that fail the guard.

19. Preserve the existing serving strategy.

20. Keep rejected candidates and their lifecycle
    metadata in MLflow.

21. Maintain rollback capability for any future
    learned production version.

22. Return to monitoring and continue observing
    the operational state.
```

The final demonstration therefore shows the complete decision process rather than simply showing a trained model.

---

# 20. Reproducibility

Phase 6 preserves reproducibility through:

* deterministic production-data simulation
* fixed simulation seed
* explicit training scripts
* explicit evaluation scripts
* MLflow experiments
* registered model versions
* model artifacts
* model signatures
* model parameters
* evaluation metrics
* lifecycle metadata
* rejection metadata
* explicit production aliases

The lifecycle state can therefore be inspected rather than inferred from undocumented local behaviour.

---

# 21. Testing

Phase 6 added tests for the new lifecycle functionality.

The final Python test suite was executed successfully:

```text
64 passed, 2 warnings
```

The warnings were dependency deprecation warnings from the testing stack.

They did not represent test failures.

Python static analysis was also executed successfully:

```text
ruff check .
All checks passed!
```

The lifecycle implementation therefore passed the project's Python test and lint gates.

---

# 22. Application Verification

The application layers were also verified.

## Application API

The following command completed successfully:

```text
npm run typecheck
```

## Web Application

The following commands completed successfully:

```text
npm run lint
npm run build
```

The production build completed successfully with the final application routes:

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

The final Next.js build successfully compiled TypeScript, collected page data, generated static pages, and completed production optimization.

---

# 23. Docker Runtime

The project uses Docker Compose for the local multi-service environment.

The final service architecture is:

```text
Web
API
Model Service
MLflow
```

with:

```text
Web             : 3000
Application API : 4000
ML Service      : 8000
MLflow          : 5000
```

Model promotion, rejection, and rollback operate through MLflow lifecycle state and therefore do not require rebuilding a Docker image merely because a model version or alias changed.

Docker rebuilds are required when the relevant application code, dependency definitions, or Docker build context changes.

The model lifecycle itself is kept separate from the immutable application container image.

---

# 24. Final Repository Structure

The completed repository is organized as:

```text
building-energy-intelligence/
│
├── apps/
│   ├── web/
│   ├── api/
│   └── model_service/
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
├── tests/
│   ├── unit/
│   ├── integration/
│   └── data/
│
├── configs/
├── scripts/
├── docker/
├── .github/workflows/
├── docs/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── reference/
│
├── models/
├── reports/
├── notebooks/
│
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

The Phase 6 lifecycle additions include:

```text
ml/lifecycle/
scripts/simulate_production_data.py
scripts/retrain_candidate.py
scripts/promote_model.py
scripts/rollback_model.py
tests/unit/test_production_simulation.py
tests/unit/test_retraining_eligibility.py
```

---

# 25. Documentation

The project's technical documentation is maintained under:

```text
docs/
```

The main documentation areas are:

```text
architecture.md
data.md
ml.md
decision_log.md
phases.md
phase6_completion.md
```

The documentation records:

* system architecture
* data scope
* feature methodology
* ML methodology
* MLOps decisions
* monitoring decisions
* lifecycle decisions
* retraining policy
* promotion policy
* baseline policy
* limitations
* phase progression

`phase6_completion.md` is the final record of the completed implementation lifecycle.

---

# 26. Data Scope

The current development dataset remains the selected BDG2 population:

```text
12 buildings
17,544 rows per building
210,528 processed rows
2016-01-01 through 2017-12-31
```

The project explicitly distinguishes:

```text
Historical Development Data
```

from:

```text
Simulated Production-like Data
```

and from:

```text
MLflow Lifecycle Metadata
```

The project does not describe the historical BDG2 dataset as live operational telemetry.

---

# 27. Final Limitations

The final project has the following explicit limitations:

1. The source dataset is historical BDG2 data.
2. The historical dataset ends in 2017.
3. Production data is simulated rather than collected from live buildings.
4. The monitoring system is local.
5. MLflow is locally hosted.
6. The selected development population contains 12 buildings.
7. Retraining is controlled rather than continuously scheduled.
8. The project does not deploy to cloud production infrastructure.
9. The project does not implement Kubernetes or distributed production infrastructure.
10. The project does not claim commercial production-scale reliability.
11. The simulated distribution shift is a controlled demonstration rather than an observed real-world shift.

These limitations are part of the project's documented scope.

---

# 28. Final Engineering Decisions

The completed system follows these principles:

```text
1. Train models reproducibly.

2. Track experiments explicitly.

3. Register model versions.

4. Keep candidate and production states separate.

5. Compare learned models against a meaningful baseline.

6. Never promote a model solely because it is the
   strongest learned model.

7. Do not allow drift alone to trigger retraining.

8. Require sufficient evidence before retraining.

9. Evaluate candidates before promotion.

10. Preserve rejected candidates and their reasons.

11. Do not overwrite production directly during training.

12. Provide rollback capability through model aliases.

13. Keep monitoring separate from retraining.

14. Keep historical data separate from simulated
    production-like data.

15. Prefer reproducibility and correctness over
    unnecessary infrastructure complexity.

16. Do not fabricate production state merely to make
    the project demonstration appear more complete.
```

---

# 29. Final Project State

The final state of the ML lifecycle is:

```text
Historical Data
      ↓
Validation
      ↓
Feature Engineering
      ↓
Model Training
      ↓
Baseline Evaluation
      ↓
MLflow Experiment Tracking
      ↓
Model Registry
      ↓
FastAPI Inference
      ↓
Application
      ↓
Monitoring
      ↓
Drift Detection
      ↓
Performance Monitoring
      ↓
Retraining Eligibility
      ↓
Simulated Production Data
      ↓
Candidate Retraining
      ↓
MLflow Candidate Experiments
      ↓
Candidate Evaluation
      ↓
Persistence Baseline Guard
      ↓
Candidate Rejection
      ↓
Production Strategy Unchanged
      ↓
Persistence Serving
      ↓
Monitoring
```

The Phase 6 candidates were:

```text
v4 — Ridge
v5 — Random Forest
v6 — HistGradientBoosting
```

All three were rejected because they did not beat the persistence baseline under the Phase 6 shifted-production evaluation.

Consequently:

```text
Learned @production model:
None

Current serving model:
Persistence

Current serving version:
baseline

Current serving mode:
baseline
```

This is the final state of the project.

---

# 30. Project Completion Statement

The Building & Energy Intelligence Platform is complete.

The final system is not merely a collection of trained models.

It is a local, reproducible ML/MLOps application demonstrating:

```text
Data
+
Machine Learning
+
Inference
+
Application Engineering
+
Experiment Tracking
+
Model Registry
+
Testing
+
CI
+
Monitoring
+
Drift Detection
+
Performance Monitoring
+
Retraining Eligibility
+
Candidate Retraining
+
Candidate Evaluation
+
Baseline-Aware Promotion
+
Model Rejection
+
Rollback Capability
```

The final lifecycle also demonstrates an important operational outcome:

```text
A trained model exists
        ↓
but it does not pass the deployment gate
        ↓
therefore it is not promoted
        ↓
the existing serving strategy remains unchanged
```

The project intentionally ends in that state.

No learned model is promoted merely for demonstration purposes.

No production state is fabricated.

No additional implementation phase is required.

**Phase 6 is complete, and the Building & Energy Intelligence Platform is complete as a portfolio-scale ML/MLOps project.**