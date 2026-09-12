from __future__ import annotations

from dataclasses import dataclass

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


@dataclass(frozen=True)
class ModelSpec:
    name: str
    pipeline: Pipeline
    feature_columns: list[str]


def make_preprocessor(
    numeric_columns: list[str],
    categorical_columns: list[str],
    dense_output: bool = False,
) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        [
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
            (
                "scaler",
                StandardScaler()
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        [
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=not dense_output,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        [
            (
                "numeric",
                numeric_pipeline,
                numeric_columns,
            ),
            (
                "categorical",
                categorical_pipeline,
                categorical_columns,
            ),
        ],
        remainder="drop",
        sparse_threshold=(
            0.0 if dense_output else 0.3
        ),
    )


def make_ridge(
    features: list[str],
    numeric: list[str],
    categorical: list[str],
    alpha: float,
) -> ModelSpec:
    pipeline = Pipeline(
        [
            (
                "preprocess",
                make_preprocessor(
                    numeric,
                    categorical,
                ),
            ),
            (
                "model",
                Ridge(alpha=alpha),
            ),
        ]
    )

    return ModelSpec(
        name="ridge",
        pipeline=pipeline,
        feature_columns=features,
    )


def make_random_forest(
    features: list[str],
    numeric: list[str],
    categorical: list[str],
    n_estimators: int,
    max_depth: int,
    min_samples_leaf: int,
    n_jobs: int,
    seed: int,
) -> ModelSpec:
    pipeline = Pipeline(
        [
            (
                "preprocess",
                make_preprocessor(
                    numeric,
                    categorical,
                ),
            ),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=n_estimators,
                    max_depth=max_depth,
                    min_samples_leaf=min_samples_leaf,
                    n_jobs=n_jobs,
                    random_state=seed,
                ),
            ),
        ]
    )

    return ModelSpec(
        name="random_forest",
        pipeline=pipeline,
        feature_columns=features,
    )


def make_hist_gradient_boosting(
    features: list[str],
    numeric: list[str],
    categorical: list[str],
    learning_rate: float,
    max_iter: int,
    max_leaf_nodes: int,
    l2_regularization: float,
    min_samples_leaf: int,
    seed: int,
) -> ModelSpec:
    pipeline = Pipeline(
        [
            (
                "preprocess",
                make_preprocessor(
                    numeric,
                    categorical,
                    dense_output=True,
                ),
            ),
            (
                "model",
                HistGradientBoostingRegressor(
                    learning_rate=learning_rate,
                    max_iter=max_iter,
                    max_leaf_nodes=max_leaf_nodes,
                    l2_regularization=l2_regularization,
                    min_samples_leaf=min_samples_leaf,
                    random_state=seed,
                ),
            ),
        ]
    )

    return ModelSpec(
        name="hist_gradient_boosting",
        pipeline=pipeline,
        feature_columns=features,
    )