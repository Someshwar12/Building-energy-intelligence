import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .config import (
    MLFLOW_MODEL_ALIAS,
    MLFLOW_MODEL_NAME,
    MLFLOW_TRACKING_URI,
    MODEL_PATH,
    MODEL_SOURCE,
    SERVICE_NAME,
    SERVICE_VERSION,
)
from .drift import (
    MIN_DRIFT_SAMPLE_COUNT,
    calculate_feature_drift,
    load_reference_profile,
)
from .inference import InferenceService
from .model_lab import (
    get_model_lab_runs,
    get_model_lab_summary,
    get_model_lab_versions,
)
from .model_loader import ModelLoader
from .monitoring import (
    MonitoringState,
    prediction_latency,
    validate_prediction_request_data,
)
from .performance import (
    DEFAULT_RECENT_WINDOW,
    PerformanceState,
)
from .schemas import (
    PerformanceOutcomeRequest,
    PredictionRequest,
    PredictionResponse,
)

logger = logging.getLogger(__name__)


model_loader = ModelLoader(
    model_path=MODEL_PATH,
    tracking_uri=MLFLOW_TRACKING_URI,
    model_name=MLFLOW_MODEL_NAME,
    model_alias=MLFLOW_MODEL_ALIAS,
    model_source=MODEL_SOURCE,
)

inference_service = InferenceService(model_loader)
monitoring_state = MonitoringState()
performance_state = PerformanceState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Initializing model service",
        extra={
            "service": SERVICE_NAME,
            "model_source": MODEL_SOURCE,
            "model_name": MLFLOW_MODEL_NAME,
            "model_alias": MLFLOW_MODEL_ALIAS,
        },
    )

    try:
        model_loader.initialize()
    except Exception:
        logger.exception(
            "Model initialization failed",
            extra={"service": SERVICE_NAME},
        )
        raise

    logger.info(
        "Model loaded successfully",
        extra={
            "service": SERVICE_NAME,
            "model_name": model_loader.model_name,
            "model_version": model_loader.model_version,
            "serving_mode": model_loader.serving_mode,
        },
    )

    yield

    logger.info(
        "Shutting down model service",
        extra={"service": SERVICE_NAME},
    )


app = FastAPI(
    title="Building Energy ML Service",
    description=(
        "Inference service for the Building & Energy "
        "Intelligence Platform."
    ),
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": SERVICE_NAME,
    }


@app.get("/ready")
def ready() -> dict[str, str]:
    if not model_loader.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Model service is not ready.",
        )

    return {
        "status": "ready",
        "model_name": model_loader.model_name,
        "model_version": model_loader.model_version,
        "serving_mode": model_loader.serving_mode,
    }


@app.get("/monitoring/summary")
def monitoring_summary() -> dict:
    monitoring = monitoring_state.snapshot()
    performance = performance_state.snapshot()

    return {
        "service": {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "status": (
                "ready"
                if model_loader.is_ready
                else "not_ready"
            ),
            "model_name": model_loader.model_name,
            "model_version": model_loader.model_version,
            "serving_mode": model_loader.serving_mode,
        },
        "monitoring": {
            **monitoring,
            "performance": performance,
        },
    }


@app.get("/monitoring/drift")
def monitoring_drift() -> dict:
    observations = monitoring_state.get_drift_observations()

    reference_profile = load_reference_profile()

    features = {}

    for feature, current_values in observations.items():
        reference = (
            reference_profile
            .get("features", {})
            .get(feature, {})
            .get("values", [])
        )

        result = calculate_feature_drift(
            feature=feature,
            current_values=current_values,
            reference_values=reference,
        )

        features[feature] = {
            "feature": feature,
            "psi": result.psi,
            "status": result.status,
            "sample_count": result.sample_count,
            "minimum_sample_count": MIN_DRIFT_SAMPLE_COUNT,
            "reference_available": (
                result.reference_available
            ),
        }

    usable = [
        feature
        for feature in features.values()
        if feature["psi"] is not None
    ]

    if any(
        feature["status"] == "critical"
        for feature in usable
    ):
        status = "critical"
    elif any(
        feature["status"] == "warning"
        for feature in usable
    ):
        status = "warning"
    elif usable:
        status = "healthy"
    else:
        status = "insufficient_data"

    reference_available = reference_profile.get(
        "available",
        True,
    )

    return {
        "status": status,
        "sample_count": (
            monitoring_state.snapshot()
            ["requests"]["successful"]
        ),
        "minimum_sample_count": 30,
        "reference": {
            "available": reference_available,
            "source": reference_profile.get("source"),
            "sample_count": reference_profile.get(
                "sample_count"
            ),
        },
        "thresholds": {
            "warning_psi": 0.10,
            "critical_psi": 0.25,
        },
        "features": features,
    }


@app.get("/model-lab/summary")
def model_lab_summary() -> dict:
    try:
        return get_model_lab_summary(
            tracking_uri=MLFLOW_TRACKING_URI,
            model_name=MLFLOW_MODEL_NAME,
            model_alias=MLFLOW_MODEL_ALIAS,
        )
    except Exception as exc:
        logger.exception(
            "Failed to load Model Lab summary",
        )
        raise HTTPException(
            status_code=500,
            detail="Model Lab summary unavailable.",
        ) from exc


@app.get("/model-lab/versions")
def model_lab_versions() -> dict:
    try:
        return {
            "model_name": MLFLOW_MODEL_NAME,
            "versions": get_model_lab_versions(
                tracking_uri=MLFLOW_TRACKING_URI,
                model_name=MLFLOW_MODEL_NAME,
            ),
        }
    except Exception as exc:
        logger.exception(
            "Failed to load Model Lab versions",
        )
        raise HTTPException(
            status_code=500,
            detail="Model Lab versions unavailable.",
        ) from exc


@app.get("/model-lab/runs")
def model_lab_runs() -> dict:
    try:
        return {
            "model_name": MLFLOW_MODEL_NAME,
            "runs": get_model_lab_runs(
                tracking_uri=MLFLOW_TRACKING_URI,
                model_name=MLFLOW_MODEL_NAME,
            ),
        }
    except Exception as exc:
        logger.exception(
            "Failed to load Model Lab runs",
        )
        raise HTTPException(
            status_code=500,
            detail="Model Lab runs unavailable.",
        ) from exc


@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def predict(
    request: PredictionRequest,
) -> PredictionResponse:
    if not model_loader.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Model service is not ready.",
        )

    start_time = prediction_latency()

    try:
        quality = validate_prediction_request_data(request)

        monitoring_state.record_quality(
            quality["status"]
        )

        response = inference_service.predict(request)

        latency_ms = (
            prediction_latency()
            - start_time
        ) * 1000

        monitoring_state.record_prediction(
            request,
            response,
            latency_ms,
        )

        persistence_baseline = (
            request.history[-1].energy_kwh
        )

        performance_state.record_prediction(
            building_id=response.building_id,
            timestamp=response.timestamp,
            prediction=response.predicted_energy_kwh,
            persistence_baseline=persistence_baseline,
            model_name=response.model_name,
            model_version=response.model_version,
            serving_mode=model_loader.serving_mode,
        )

        logger.info(
            "Prediction completed",
            extra={
                "building_id": request.building_id,
                "timestamp": request.timestamp.isoformat(),
                "model_name": response.model_name,
                "model_version": response.model_version,
                "latency_ms": latency_ms,
                "data_quality_status": quality["status"],
            },
        )

        return response

    except ValueError as exc:
        monitoring_state.record_failure(
            str(exc)
        )

        logger.warning(
            "Prediction request rejected: %s",
            exc,
            extra={
                "building_id": request.building_id,
            },
        )

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception:
        monitoring_state.record_failure(
            "Unexpected prediction failure."
        )

        logger.exception(
            "Unexpected prediction failure",
            extra={
                "building_id": request.building_id,
            },
        )

        raise HTTPException(
            status_code=500,
            detail="Prediction failed.",
        ) from None


@app.get("/monitoring/performance")
def monitoring_performance(
    recent_window: int = DEFAULT_RECENT_WINDOW,
) -> dict:
    try:
        return performance_state.performance_report(
            recent_window=recent_window,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@app.post("/monitoring/outcomes")
def record_monitoring_outcome(
    request: PerformanceOutcomeRequest,
) -> dict:
    try:
        observation = performance_state.record_outcome(
            building_id=request.building_id,
            timestamp=request.timestamp,
            actual_energy_kwh=request.actual_energy_kwh,
        )

        return {
            "status": "recorded",
            "outcome": {
                "building_id": observation.building_id,
                "timestamp": observation.timestamp,
                "prediction": observation.prediction,
                "actual": observation.actual,
                "persistence_baseline": (
                    observation.persistence_baseline
                ),
                "absolute_error": observation.absolute_error,
                "squared_error": observation.squared_error,
                "model_name": observation.model_name,
                "model_version": observation.model_version,
                "serving_mode": observation.serving_mode,
            },
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc