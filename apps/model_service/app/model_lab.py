from __future__ import annotations

from pathlib import Path
from typing import Any

import mlflow
import pandas as pd
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException

BASELINE_REPORT_PATH = (
    Path(__file__).resolve().parents[3]
    / "reports"
    / "generated"
    / "phase1_baseline_results.csv"
)


def _client(tracking_uri: str) -> MlflowClient:
    mlflow.set_tracking_uri(tracking_uri)
    return MlflowClient(tracking_uri=tracking_uri)


def _run_payload(
    client: MlflowClient,
    run_id: str,
) -> dict[str, Any]:
    run = client.get_run(run_id)

    return {
        "run_id": run.info.run_id,
        "experiment_id": run.info.experiment_id,
        "status": run.info.status,
        "start_time": run.info.start_time,
        "end_time": run.info.end_time,
        "params": dict(run.data.params),
        "metrics": dict(run.data.metrics),
        "tags": dict(run.data.tags),
    }


def _version_payload(
    client: MlflowClient,
    model_version,
) -> dict[str, Any]:
    run = client.get_run(model_version.run_id)

    tags = dict(run.data.tags)

    aliases = list(
        getattr(model_version, "aliases", None)
        or []
    )

    return {
        "version": str(model_version.version),
        "model_name": model_version.name,
        "run_id": model_version.run_id,
        "status": model_version.status,
        "aliases": aliases,
        "description": model_version.description,
        "created_at": model_version.creation_timestamp,
        "updated_at": model_version.last_updated_timestamp,
        "model_family": tags.get("model_family"),
        "validation_status": tags.get(
            "validation_status",
        ),
        "lifecycle_status": tags.get(
            "lifecycle_status",
        ),
        "promotion_metric": tags.get(
            "promotion_metric",
        ),
        "promotion_reason": tags.get(
            "promotion_reason",
        ),
        "baseline_guard": tags.get(
            "baseline_guard",
        ),
        "baseline_model": tags.get(
            "baseline_model",
        ),
        "baseline_validation_nmae": tags.get(
            "baseline_validation_nmae",
        ),
        "rejection_reason": tags.get(
            "rejection_reason",
        ),
        "metrics": dict(run.data.metrics),
        "params": dict(run.data.params),
        "tags": tags,
    }


def _load_baseline_results() -> list[dict[str, Any]]:
    if not BASELINE_REPORT_PATH.exists():
        return []

    try:
        dataframe = pd.read_csv(BASELINE_REPORT_PATH)

        results: list[dict[str, Any]] = []

        for row in dataframe.to_dict(
            orient="records",
        ):
            metrics: dict[str, float] = {}

            for key, value in row.items():
                if key == "baseline":
                    continue

                if value is None:
                    continue

                try:
                    metrics[key] = float(value)
                except (TypeError, ValueError):
                    continue

            results.append(
                {
                    "baseline": str(row["baseline"]),
                    "metrics": metrics,
                }
            )

        return results

    except (
        OSError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
    ):
        return []


def _baseline_payload() -> dict[str, Any]:
    results = _load_baseline_results()

    persistence = next(
        (
            item
            for item in results
            if item["baseline"] == "pred_persistence"
        ),
        None,
    )

    return {
        "available": persistence is not None,
        "name": "persistence",
        "display_name": "Persistence",
        "strategy": (
            "Use the latest observed energy value "
            "as the next-hour prediction."
        ),
        "metrics": (
            persistence["metrics"]
            if persistence
            else {}
        ),
        "all_baselines": results,
        "source": (
            "reports/generated/phase1_baseline_results.csv"
            if persistence
            else None
        ),
    }


def get_model_lab_summary(
    tracking_uri: str,
    model_name: str,
    model_alias: str,
) -> dict[str, Any]:
    client = _client(tracking_uri)

    try:
        production = client.get_model_version_by_alias(
            model_name,
            model_alias,
        )

        production_payload = {
            "model_name": production.name,
            "version": str(production.version),
            "alias": model_alias,
            "run_id": production.run_id,
            "serving_mode": "mlflow",
        }

    except MlflowException:
        production_payload = {
            "model_name": "persistence",
            "version": "baseline",
            "alias": None,
            "run_id": None,
            "serving_mode": "baseline",
        }

    versions = list(
        client.search_model_versions(
            f"name='{model_name}'",
        )
    )

    versions.sort(
        key=lambda item: int(item.version),
        reverse=True,
    )

    version_payloads = [
        _version_payload(client, version)
        for version in versions
    ]

    evaluated = [
        version
        for version in version_payloads
        if version["validation_status"]
        == "evaluated"
    ]

    rejected = [
        version
        for version in version_payloads
        if version["lifecycle_status"]
        == "rejected"
    ]

    candidate = next(
        (
            version
            for version in version_payloads
            if "candidate" in version["aliases"]
        ),
        None,
    )

    return {
        "model_name": model_name,
        "production": production_payload,
        "candidate": (
            {
                "version": candidate["version"],
                "model_family": candidate[
                    "model_family"
                ],
            }
            if candidate
            else None
        ),
        "registered_versions": len(
            version_payloads,
        ),
        "evaluated_versions": len(
            evaluated,
        ),
        "rejected_versions": len(
            rejected,
        ),
        "baseline": _baseline_payload(),
        "versions": version_payloads,
    }


def get_model_lab_versions(
    tracking_uri: str,
    model_name: str,
) -> list[dict[str, Any]]:
    client = _client(tracking_uri)

    versions = list(
        client.search_model_versions(
            f"name='{model_name}'",
        )
    )

    versions.sort(
        key=lambda item: int(item.version),
        reverse=True,
    )

    return [
        _version_payload(client, version)
        for version in versions
    ]


def get_model_lab_runs(
    tracking_uri: str,
    model_name: str,
) -> list[dict[str, Any]]:
    client = _client(tracking_uri)

    versions = list(
        client.search_model_versions(
            f"name='{model_name}'",
        )
    )

    run_ids = []

    for version in versions:
        if version.run_id not in run_ids:
            run_ids.append(version.run_id)

    runs = [
        _run_payload(client, run_id)
        for run_id in run_ids
    ]

    runs.sort(
        key=lambda run: (
            run["start_time"] or 0
        ),
        reverse=True,
    )

    return runs