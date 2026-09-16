from __future__ import annotations

from pathlib import Path

import joblib
import mlflow
from mlflow import MlflowClient


class ModelLoader:
    """Loads and owns the configured ML model for the service lifetime."""

    def __init__(
        self,
        model_path: Path,
        tracking_uri: str | None = None,
        model_name: str | None = None,
        model_alias: str | None = None,
        model_source: str = "local",
    ) -> None:
        self.model_path = model_path
        self.tracking_uri = tracking_uri
        self.model_name_config = model_name
        self.model_alias = model_alias
        self.model_source = model_source

        self._artifact = None
        self._model = None
        self._model_name = None
        self._model_version = None
        self._metadata: dict = {}
        self._feature_columns: list[str] = []
        self._serving_mode = None

    def initialize(self) -> None:
        if self.model_source == "mlflow":
            self._initialize_from_mlflow()
        elif self.model_source == "local":
            self._initialize_from_local()
        else:
            raise ValueError(
                "MODEL_SOURCE must be either 'mlflow' or 'local'."
            )

    def _initialize_from_mlflow(self) -> None:
        if not self.tracking_uri:
            raise ValueError(
                "MLFLOW_TRACKING_URI is required for MLflow model loading."
            )

        if not self.model_name_config:
            raise ValueError(
                "MLFLOW_MODEL_NAME is required for MLflow model loading."
            )

        if not self.model_alias:
            raise ValueError(
                "MLFLOW_MODEL_ALIAS is required for MLflow model loading."
            )

        mlflow.set_tracking_uri(self.tracking_uri)

        client = MlflowClient(
            tracking_uri=self.tracking_uri,
        )

        try:
            model_version = client.get_model_version_by_alias(
                self.model_name_config,
                self.model_alias,
            )
        except Exception as exc:
            if self._is_missing_alias_error(exc):
                self._initialize_baseline()
                return

            raise RuntimeError(
                "Unable to resolve MLflow model "
                f"{self.model_name_config}@{self.model_alias}."
            ) from exc

        model_uri = (
            f"models:/{self.model_name_config}"
            f"@{self.model_alias}"
        )

        try:
            model = mlflow.sklearn.load_model(model_uri)
        except Exception as exc:
            raise RuntimeError(
                "Unable to load MLflow model from "
                f"{model_uri}."
            ) from exc

        model_info = mlflow.models.get_model_info(model_uri)

        feature_columns = self._extract_feature_columns(
            model_info,
        )

        run = client.get_run(model_version.run_id)

        metadata = dict(run.data.tags)

        self._model = model
        self._model_name = self._extract_model_name(
            metadata,
        )
        self._model_version = str(model_version.version)
        self._metadata = metadata
        self._feature_columns = feature_columns
        self._serving_mode = "mlflow"

    def _initialize_baseline(self) -> None:
        self._artifact = None
        self._model = None
        self._model_name = "persistence"
        self._model_version = "baseline"
        self._metadata = {
            "serving_mode": "baseline",
            "baseline": "persistence",
            "reason": "No MLflow production alias is available.",
        }
        self._feature_columns = []
        self._serving_mode = "baseline"

    def _initialize_from_local(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found: {self.model_path}"
            )

        try:
            artifact = joblib.load(self.model_path)
        except Exception as exc:
            raise ValueError(
                f"Unable to load model artifact: {self.model_path}"
            ) from exc

        if not isinstance(artifact, dict):
            raise TypeError("Model artifact must be a dictionary.")

        required_keys = {
            "model_name",
            "model",
            "feature_columns",
            "metadata",
        }

        missing = required_keys - artifact.keys()

        if missing:
            raise ValueError(
                "Model artifact is missing required keys: "
                f"{sorted(missing)}"
            )

        self._artifact = artifact
        self._model = artifact["model"]
        self._model_name = artifact["model_name"]
        self._model_version = self._extract_local_version(
            artifact,
        )
        self._metadata = artifact["metadata"]
        self._feature_columns = artifact["feature_columns"]
        self._serving_mode = "local"

    @staticmethod
    def _is_missing_alias_error(exc: Exception) -> bool:
        message = str(exc).lower()

        return (
            "alias" in message
            and (
                "not found" in message
                or "invalid_parameter_value" in message
            )
        )

    @staticmethod
    def _extract_feature_columns(
        model_info,
    ) -> list[str]:
        signature = model_info.signature

        if signature is None or signature.inputs is None:
            raise ValueError(
                "Registered MLflow model does not expose "
                "an input signature."
            )

        columns = []

        for column in signature.inputs.inputs:
            if column.name is None:
                raise ValueError(
                    "MLflow model input signature contains "
                    "an unnamed feature."
                )

            columns.append(str(column.name))

        if not columns:
            raise ValueError(
                "Registered MLflow model input signature "
                "contains no features."
            )

        return columns

    @staticmethod
    def _extract_model_name(
        metadata: dict,
    ) -> str:
        model_name = metadata.get("model_name")

        if not model_name:
            return "mlflow-model"

        return str(model_name)

    @staticmethod
    def _extract_local_version(
        artifact: dict,
    ) -> str:
        metadata = artifact["metadata"]

        return str(
            metadata.get(
                "model_version",
                metadata.get("phase", "local"),
            )
        )

    @property
    def is_ready(self) -> bool:
        return self._serving_mode is not None

    @property
    def model(self):
        if self._model is None:
            raise RuntimeError(
                "A learned model is not currently loaded."
            )

        return self._model

    @property
    def model_name(self) -> str:
        if self._model_name is None:
            raise RuntimeError("Model is not initialized.")

        return self._model_name

    @property
    def model_version(self) -> str:
        if self._model_version is None:
            raise RuntimeError("Model is not initialized.")

        return self._model_version

    @property
    def metadata(self) -> dict:
        return self._metadata

    @property
    def feature_columns(self) -> list[str]:
        return self._feature_columns

    @property
    def serving_mode(self) -> str:
        if self._serving_mode is None:
            raise RuntimeError("Model is not initialized.")

        return self._serving_mode