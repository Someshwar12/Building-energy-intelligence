# Phase 3 — Application Platform

## Status

**Completed**

Phase 3 transforms the project from a machine-learning inference service into a functional web application platform.

The phase introduces a clear separation between:

- frontend user experience
- application-level API
- ML inference service
- machine-learning model artifact

The resulting architecture is:

```text
Next.js / React
      │
      ▼
Node.js / Express
      │
      ▼
FastAPI ML Service
      │
      ▼
Phase 1 Random Forest Model
````

---

## Objectives

The objectives of Phase 3 were to:

* build a functional web interface
* expose building-level information
* expose historical energy consumption
* visualize consumption data
* integrate the existing ML inference service
* provide building-level forecasting
* establish a clean frontend → application API → ML service boundary
* introduce application-level loading, empty, and error states
* validate the complete application stack

Phase 3 deliberately does **not** introduce the MLOps infrastructure planned for later phases.

---

## Technology Stack

### Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Recharts

### Application API

* Node.js
* Express
* TypeScript
* hyparquet

### ML Service

The existing Phase 2 FastAPI service remains responsible for:

* model loading
* request validation
* feature construction
* ML inference
* model metadata

### Data

The application uses:

```text
data/processed/phase1_features.parquet
```

as the historical consumption source.

Building metadata is exported to:

```text
apps/api/src/data/buildings.json
```

---

## Application Architecture

Phase 3 introduces the application layer around the existing ML service.

```text
┌─────────────────────────────────────────────┐
│               Next.js Frontend              │
│                                             │
│  Overview                                   │
│  Building Details                           │
│  Consumption Visualization                  │
│  Forecast Display                           │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│            Node.js / Express API            │
│                                             │
│  Building Routes                            │
│  Consumption Routes                         │
│  Prediction Routes                          │
│  Application-level orchestration            │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│             FastAPI ML Service              │
│                                             │
│  Request validation                         │
│  Feature construction                       │
│  Model loading                              │
│  Inference                                  │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│          Phase 1 Random Forest Model        │
└─────────────────────────────────────────────┘
```

This separation ensures that the frontend does not directly depend on the ML implementation.

---

## Frontend

The frontend is located at:

```text
apps/web/
```

The main application provides:

* platform overview
* building listing
* building detail pages
* building metadata
* historical consumption analysis
* next-hour forecast display
* loading states
* error states
* empty states
* responsive layouts

The overview page provides access to the available buildings.

The building detail page provides a more detailed analytical view.

---

## Building Detail Page

The building detail page follows this structure:

```text
Building Header
       │
       ├── Building Metadata
       │
       ├── Consumption ───────── Forecast
       │
       └── Building Profile
```

The consumption and forecast sections are displayed together because they represent the primary analytical workflow.

The building profile is displayed underneath as supporting contextual information.

On smaller screens the layout becomes vertically stacked.

---

## Consumption Analysis

Historical electricity consumption is retrieved through the application API.

The frontend displays the data using a Recharts-based line chart.

The current implementation demonstrates a historical December 2017 window.

The application retrieves:

* timestamp
* energy consumption in kWh

for the selected building and requested time range.

The consumption repository reads from the canonical Phase 1 Parquet dataset.

---

## Building Metadata

The application exposes the building metadata selected during Phase 1.

The current application contains the 12 selected buildings.

Building information includes fields such as:

* building identifier
* site
* primary use
* floor area
* square footage
* timezone
* year built
* number of floors
* occupants
* heating type
* LEED level
* site EUI

The Node application provides repository and service layers around this metadata.

---

## Application API

The application API is located at:

```text
apps/api/
```

The API provides the application boundary between the frontend and the ML service.

### Building endpoints

```text
GET /api/buildings
GET /api/buildings/:buildingId
```

These endpoints provide building discovery and building-level metadata.

### Consumption endpoint

```text
GET /api/buildings/:buildingId/consumption
```

The endpoint supports retrieving historical consumption for a building over a requested time range.

### Forecast endpoint

```text
GET /api/buildings/:buildingId/forecast
```

The forecast endpoint prepares the required historical context and forwards the inference request to the FastAPI ML service.

---

## End-to-End Prediction Flow

The forecasting workflow is:

```text
Building Detail Page
        │
        ▼
Next.js API Client
        │
        ▼
Express Forecast Route
        │
        ▼
Prediction Repository
        │
        ▼
168-hour historical context
        │
        ▼
FastAPI /predict
        │
        ▼
Random Forest Model
        │
        ▼
Prediction Response
        │
        ▼
Express API
        │
        ▼
Forecast Card
```

The Node application prepares the request required by the Phase 2 ML service.

The prediction request contains the building metadata, weather context, target timestamp, and required historical energy observations.

The FastAPI service then performs the actual model inference.

---

## Forecast Response

The forecast response contains:

```text
building_id
timestamp
predicted_energy_kwh
model_name
model_version
```

The current model metadata is:

```text
model_name: random_forest
model_version: phase1
```

This preserves the model identity established by the earlier ML phases.

---

## Prediction Context

The application retrieves the historical context required by the ML service before making a prediction.

The current implementation prepares:

* building metadata
* weather variables
* target timestamp
* historical energy observations

The prediction context contains exactly the historical window required by the Phase 2 inference contract.

This keeps the feature and input contract consistent across the application and ML layers.

---

## Frontend API Client

Frontend API communication is centralized under:

```text
apps/web/src/lib/api.ts
```

Typed interfaces are used for application responses including:

* `Building`
* `ConsumptionPoint`
* `Forecast`

This prevents UI components from depending directly on backend implementation details.

---

## Application Error Handling

Phase 3 introduces explicit application-level handling for common failure states.

The frontend handles:

* building loading
* consumption loading
* forecast loading
* building retrieval failures
* consumption retrieval failures
* forecast retrieval failures
* empty consumption results
* unavailable ML inference

The application avoids exposing internal backend exceptions directly to the user.

---

## Current Data Flow

The overall application data flow is:

```text
BDG2 Dataset
     │
     ▼
Phase 1 Feature Dataset
     │
     ├──────────────► Historical Consumption
     │                       │
     │                       ▼
     │                 Express API
     │                       │
     │                       ▼
     │                  Next.js UI
     │
     └──────────────► Prediction Context
                             │
                             ▼
                       Express API
                             │
                             ▼
                      FastAPI ML Service
                             │
                             ▼
                    Random Forest Model
                             │
                             ▼
                       Forecast Result
                             │
                             ▼
                         Next.js UI
```

---

## Repository Structure Added in Phase 3

```text
apps/
├── api/
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── config/
│       │   └── env.ts
│       ├── data/
│       │   └── buildings.json
│       ├── repositories/
│       │   ├── buildingRepository.ts
│       │   ├── consumptionRepository.ts
│       │   └── predictionRepository.ts
│       ├── routes/
│       │   ├── buildings.ts
│       │   ├── consumption.ts
│       │   ├── index.ts
│       │   └── predictions.ts
│       ├── services/
│       │   ├── buildingService.ts
│       │   ├── consumptionService.ts
│       │   └── predictionService.ts
│       └── server.ts
│
└── web/
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── buildings/
        │   │   └── [buildingId]/
        │   │       └── page.tsx
        │   ├── globals.css
        │   ├── layout.tsx
        │   └── page.tsx
        ├── components/
        │   └── ConsumptionChart.tsx
        └── lib/
            └── api.ts
```

Additional Phase 3 data preparation:

```text
scripts/
└── phase3_export_buildings.py
```

---

## Validation

Phase 3 was validated through the existing Python test suite and the frontend/backend build checks.

### Python tests

```text
pytest -p no:cacheprovider
```

Result:

```text
PASS
```

All existing Python tests passed successfully.

### Node API type checking

```text
npm run typecheck
```

Result:

```text
PASS
```

### Node API production build

```text
npm run build
```

Result:

```text
PASS
```

### Next.js linting

```text
npm run lint
```

Result:

```text
PASS
```

### Next.js production build

```text
npm run build
```

Result:

```text
PASS
```

The complete Phase 3 stack therefore passed its validation checks.

---

## Scope Boundary

Phase 3 establishes the application platform.

It does **not** yet implement:

* Docker
* MongoDB persistence
* MLflow
* experiment tracking
* model registry
* champion/challenger management
* automated model promotion
* data drift monitoring
* prediction performance monitoring
* automated retraining
* CI/CD
* cloud deployment

These capabilities belong to subsequent phases.

---

## Forecasting Limitation

The current forecast demonstration uses historical BDG2 data.

The demonstrated prediction timestamp is therefore historical rather than a live future timestamp.

The model is nevertheless performing the same one-step-ahead prediction task established during Phase 1 and exposed through the Phase 2 inference service.

The current implementation should therefore be understood as an **application-level demonstration of the forecasting pipeline**, not as a live operational forecasting system.

A later production-oriented implementation will connect the prediction workflow to continuously refreshed observations and explicitly distinguish historical inference from live forecasting.

## Phase 3 Outcome

Phase 3 successfully converts the project from a standalone ML pipeline and inference service into a functional application platform.

The project now has:

* a Next.js web application
* a Node.js/Express application API
* a FastAPI ML inference service
* a clean service boundary
* typed frontend/API contracts
* building discovery
* building-level metadata
* historical consumption analysis
* consumption visualization
* end-to-end ML forecasting
* structured prediction responses
* loading states
* empty states
* error states
* validated production builds
