# Project Phases

## 1. Purpose

This document defines the development roadmap for the Building & Energy Intelligence Platform.

The project is intentionally developed in controlled phases so that each layer is implemented, tested, documented, and validated before the next layer is introduced.

The overall progression is:

    Data
      ↓
    Features
      ↓
    Machine Learning
      ↓
    Inference API
      ↓
    Application Backend
      ↓
    Frontend
      ↓
    Containerization
      ↓
    Experiment Tracking
      ↓
    Model Lifecycle
      ↓
    Monitoring
      ↓
    Automated Retraining
      ↓
    Deployment

The phases are deliberately separated to avoid building infrastructure before the underlying ML system is reliable.

---

## 2. Phase 0 — Data Proof and Dataset Understanding

### Objective

Establish that the selected BDG2 data is understood, accessible, structurally valid, and suitable for the forecasting problem.

### Scope

- Inspect raw electricity data
- Inspect building metadata
- Inspect weather data
- Understand timestamps and granularity
- Identify buildings and sites
- Check missingness
- Check duplicate keys
- Verify hourly structure
- Verify relationships between electricity, metadata, and weather
- Produce an initial data-quality report

### Outcome

A validated understanding of the raw dataset and a reproducible data-ingestion starting point.

### Status

Completed.

---

## 3. Phase 1 — Feature Engineering and ML Benchmark

### Objective

Create the canonical forecasting dataset and establish an evidence-based ML benchmark.

### Scope

- Build the canonical feature dataset
- Join electricity, metadata, and weather
- Create calendar features
- Create cyclical time features
- Create historical lag features
- Create rolling statistics
- Create heating/cooling degree-hour features
- Create the next-hour target
- Validate temporal alignment
- Prevent target leakage
- Perform chronological train/validation/test splitting
- Evaluate persistence baseline
- Evaluate previous-day baseline
- Evaluate previous-week baseline
- Train Random Forest
- Train HistGradientBoosting
- Train Ridge
- Compare models using multiple metrics
- Perform building-level error analysis
- Save the Random Forest artifact

### Key Decision

The persistence baseline outperformed the evaluated ML models.

Therefore:

    Champion  = Persistence
    Challenger = Random Forest

Random Forest is retained as the ML challenger and Phase 2 serving artifact.

### Status

Completed.

---

## 4. Phase 2 — ML Inference Service

### Objective

Expose the Phase 1 ML model through a standalone production-style inference API.

### Scope

- Create standalone FastAPI service
- Define request schemas
- Define response schemas
- Validate incoming data
- Validate historical context
- Reconstruct model features
- Maintain feature parity with Phase 1
- Load model artifact once at startup
- Validate model artifact structure
- Run inference
- Return structured predictions
- Add health endpoint
- Add readiness endpoint
- Add structured logging
- Expose OpenAPI documentation
- Add unit and integration tests
- Test real HTTP inference

### Architecture Boundary

The ML service is independent from the future application backend.

Current:

    Client
      ↓
    FastAPI ML Service
      ↓
    Random Forest

Future:

    React
      ↓
    Node/Express API
      ↓
    FastAPI ML Service
      ↓
    Model

The Node/Express backend is intentionally not implemented in this phase.

### Status

Completed.

---

## 5. Phase 3 — Application Backend

### Objective

Introduce the application-facing backend that separates product/application concerns from ML inference.

### Planned scope

- Node.js / Express backend
- Application API routes
- Request orchestration
- Building and metadata endpoints
- Prediction request orchestration
- Communication with FastAPI ML service
- API-level validation
- Error handling
- Configuration management
- Separation between application API and ML API
- Backend tests

### Intended boundary

    React
      ↓
    Node/Express
      ↓
    FastAPI
      ↓
    ML model

The frontend should not directly depend on model internals.

### Status

Not started.

---

## 6. Phase 4 — Web Dashboard

### Objective

Build the user-facing interface for exploring building energy behavior and predictions.

### Planned scope

- React
- Next.js application
- Building selection
- Energy history visualization
- Forecast visualization
- Building metadata
- Weather context
- Prediction results
- API integration
- Loading states
- Error states
- Responsive UI
- Basic dashboard-level testing

### Planned user flow

    Select building
        ↓
    Inspect historical energy
        ↓
    Request forecast
        ↓
    View predicted next-hour consumption
        ↓
    Compare prediction with historical behavior

### Status

Not started.

---

## 7. Phase 5 — Containerization and Local System Integration

### Objective

Make the complete application reproducible as a multi-service local system.

### Planned scope

- Dockerfiles
- Docker Compose
- React/web service
- Node/Express API service
- FastAPI ML service
- Environment configuration
- Service-to-service networking
- Health checks
- Reproducible local startup
- Container-level integration testing

### Target architecture

    Browser
       ↓
    Web container
       ↓
    API container
       ↓
    ML service container
       ↓
    Model artifact

### Status

Not started.

---

## 8. Phase 6 — Experiment Tracking

### Objective

Make ML experiments reproducible and comparable beyond manually recorded results.

### Planned scope

- Experiment tracking
- Parameter logging
- Metric logging
- Dataset/version references
- Model artifact tracking
- Run comparison
- Experiment metadata
- Reproducible training configuration

A tracking system such as MLflow may be introduced at this stage.

The exact tool should be selected based on the requirements and local complexity at implementation time.

### Status

Not started.

---

## 9. Phase 7 — Model Registry and Lifecycle

### Objective

Introduce controlled model versioning and promotion.

### Planned scope

- Model versions
- Model metadata
- Model registry
- Candidate models
- Champion model
- Challenger model
- Evaluation gates
- Promotion rules
- Rollback capability
- Production model selection

The system should make model promotion an explicit decision rather than automatically replacing the current model.

### Conceptual lifecycle

    Training
       ↓
    Evaluation
       ↓
    Candidate
       ↓
    Validation gate
       ↓
    Challenger
       ↓
    Promotion decision
       ↓
    Champion

### Status

Not started.

---

## 10. Phase 8 — Production Monitoring

### Objective

Observe the behavior of the deployed ML system over time.

### Planned scope

### Service monitoring

- Request counts
- Latency
- Error rates
- Health status
- Readiness status

### Data monitoring

- Missing values
- Invalid values
- Feature distributions
- Input volume
- Data-quality violations

### Prediction monitoring

- Prediction distribution
- Prediction volume
- Building-level prediction behavior
- Unexpected prediction changes

### Performance monitoring

When actual future energy becomes available:

- MAE
- RMSE
- NMAE
- Building-level performance
- Performance by time period

### Status

Not started.

---

## 11. Phase 9 — Drift Detection

### Objective

Detect when production data differs materially from the data used during model development.

### Planned scope

- Feature distribution monitoring
- Data-quality drift
- Prediction drift
- Building-level drift
- Weather distribution changes
- Seasonal changes
- Threshold-based alerts
- Drift reports

Drift detection should not automatically imply that retraining is necessary.

A detected distribution change is an investigation signal, not proof that the model has failed.

### Status

Not started.

---

## 12. Phase 10 — Controlled Retraining

### Objective

Create a safe model improvement loop based on production evidence.

### Planned scope

- Collect validated production observations
- Construct updated training data
- Re-run feature pipeline
- Train candidate models
- Evaluate against the current champion
- Compare against persistence
- Perform regression checks
- Register candidate artifact
- Apply promotion criteria
- Promote only when evaluation requirements are satisfied

### Intended loop

    Production data
        ↓
    Validation
        ↓
    Retraining
        ↓
    Evaluation
        ↓
    Champion comparison
        ↓
    Promotion gate
        ↓
    New champion or rejection

Retraining must not automatically replace the production model merely because new data exists.

### Status

Not started.

---

## 13. Phase 11 — CI/CD and Deployment

### Objective

Automate software validation and prepare the platform for deployment.

### Planned scope

- GitHub Actions
- Automated linting
- Automated tests
- Build verification
- Container image validation
- Integration tests
- Model artifact validation
- Deployment workflow
- Environment-specific configuration
- Production deployment

CI/CD should be introduced after the application and ML architecture are sufficiently stable.

### Status

Not started.

---

## 14. Phase 12 — Advanced ML

### Objective

Improve forecasting capability only after the complete system is measurable and operational.

### Potential scope

- Stronger feature engineering
- More sophisticated forecasting models
- Building-specific models
- Global models across buildings
- Multi-step forecasting
- Quantile/probabilistic forecasting
- Better handling of missing observations
- Hyperparameter optimization
- Model ensembles
- Forecast uncertainty
- Additional external variables

Advanced ML should be justified by measured weaknesses in the existing system.

The project should not introduce complexity merely for technological novelty.

### Status

Not started.

---

## 15. Phase Completion Rule

Each phase follows the same development cycle:

    Define
      ↓
    Implement
      ↓
    Test
      ↓
    Inspect
      ↓
    Document
      ↓
    Git commit
      ↓
    Git push
      ↓
    Proceed to next phase

A phase is considered complete only when its intended functionality has been validated.

---

## 16. Scope Control

The project deliberately avoids implementing all infrastructure simultaneously.

The following are explicitly deferred until their corresponding phases:

- Node/Express → Phase 3
- React/Next.js → Phase 4
- Docker → Phase 5
- Experiment tracking → Phase 6
- Model registry → Phase 7
- Monitoring → Phase 8
- Drift detection → Phase 9
- Retraining → Phase 10
- CI/CD → Phase 11
- Advanced ML → Phase 12

This prevents premature infrastructure complexity and keeps each development checkpoint independently testable.

---

## 17. Current Position

Completed:

    Phase 0 ✓
    Phase 1 ✓
    Phase 2 ✓

Current architecture:

    BDG2
      ↓
    Validation
      ↓
    Feature Engineering
      ↓
    ML Benchmark
      ↓
    Random Forest Artifact
      ↓
    FastAPI Inference Service

Next:

    Phase 3 — Application Backend

The project is therefore transitioning from the validated ML/inference foundation into the application architecture layer.