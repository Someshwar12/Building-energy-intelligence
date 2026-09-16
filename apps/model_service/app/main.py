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
from .inference import InferenceService
from .model_loader import ModelLoader
from .schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)

model_loader = ModelLoader(
    model_path=MODEL_PATH,
    tracking_uri=MLFLOW_TRACKING_URI,
    model_name=MLFLOW_MODEL_NAME,
    model_alias=MLFLOW_MODEL_ALIAS,
    model_source=MODEL_SOURCE,
)

inference_service = InferenceService(model_loader)


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

    try:
        response = inference_service.predict(request)

        logger.info(
            "Prediction completed",
            extra={
                "building_id": request.building_id,
                "timestamp": request.timestamp.isoformat(),
                "model_name": response.model_name,
                "model_version": response.model_version,
            },
        )

        return response

    except ValueError as exc:
        logger.warning(
            "Prediction request rejected: %s",
            exc,
            extra={"building_id": request.building_id},
        )

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected prediction failure",
            extra={"building_id": request.building_id},
        )

        raise HTTPException(
            status_code=500,
            detail="Prediction failed.",
        ) from exc