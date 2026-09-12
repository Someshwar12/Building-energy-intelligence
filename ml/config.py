from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Phase1Config:
    raw_root: Path
    interim_root: Path
    processed_root: Path
    reports_root: Path

    n_buildings: int
    min_coverage_ratio: float
    max_missing_ratio: float
    seed: int

    train_start: str
    train_end: str
    validation_start: str
    validation_end: str
    test_start: str
    test_end: str
    frequency: str

    target_name: str
    horizon_hours: int

    lags: tuple[int, ...]
    rolling_windows: tuple[int, ...]
    weather_columns: tuple[str, ...]
    degree_day_base_c: float


def load_project_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def phase1_config(path: str | Path) -> Phase1Config:
    cfg = load_project_config(path)

    project = cfg["project"]
    data = cfg["data"]
    phase1 = cfg["phase1"]
    time_cfg = phase1["time"]
    target = phase1["target"]
    features = phase1["features"]

    return Phase1Config(
        raw_root=Path(data["raw_root"]),
        interim_root=Path(data["interim_root"]),
        processed_root=Path(data["processed_root"]),
        reports_root=Path(data["reports_root"]),
        n_buildings=int(phase1["n_buildings"]),
        min_coverage_ratio=float(phase1["min_coverage_ratio"]),
        max_missing_ratio=float(phase1["max_missing_ratio"]),
        seed=int(project["seed"]),
        train_start=time_cfg["train_start"],
        train_end=time_cfg["train_end"],
        validation_start=time_cfg["validation_start"],
        validation_end=time_cfg["validation_end"],
        test_start=time_cfg["test_start"],
        test_end=time_cfg["test_end"],
        frequency=time_cfg["frequency"],
        target_name=target["name"],
        horizon_hours=int(target["horizon_hours"]),
        lags=tuple(int(x) for x in features["lags"]),
        rolling_windows=tuple(int(x) for x in features["rolling_windows"]),
        weather_columns=tuple(features["weather"]),
        degree_day_base_c=float(features["degree_day_base_c"]),
    )