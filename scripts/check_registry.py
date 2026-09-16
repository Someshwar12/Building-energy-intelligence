import mlflow
from mlflow import MlflowClient

mlflow.set_tracking_uri("http://127.0.0.1:5000")

client = MlflowClient()

model = client.get_registered_model(
    "building-energy-forecast"
)

print("ALIASES:", model.aliases)

versions = client.search_model_versions(
    "name='building-energy-forecast'"
)

print(
    "VERSIONS:",
    [
        (
            version.version,
            version.tags.get("lifecycle_status"),
            version.tags.get("baseline_guard"),
        )
        for version in versions
    ],
)