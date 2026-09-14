from pathlib import Path

import joblib


class ModelLoader:
    """Loads and owns the Phase 1 ML artifact for the service lifetime."""

    def __init__(self, model_path: Path) -> None:
        self.model_path = model_path
        self._artifact = None

    def initialize(self) -> None:
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
                f"Model artifact is missing required keys: "
                f"{sorted(missing)}"
            )

        self._artifact = artifact

    @property
    def is_ready(self) -> bool:
        return self._artifact is not None

    @property
    def model(self):
        if not self.is_ready:
            raise RuntimeError("Model is not initialized.")

        return self._artifact["model"]

    @property
    def model_name(self) -> str:
        return self._artifact["model_name"]

    @property
    def model_version(self) -> str:
        metadata = self.metadata

        return str(
            metadata.get(
                "model_version",
                metadata.get("phase", "unknown"),
            )
        )

    @property
    def metadata(self) -> dict:
        return self._artifact["metadata"]

    @property
    def feature_columns(self) -> list[str]:
        return self._artifact["feature_columns"]