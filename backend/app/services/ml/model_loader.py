"""Load and cache trained sklearn models."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib

from app.core.config import settings

# Legacy single model (backward compatible)
MODEL_FILENAME = "logistic_regression.joblib"
METADATA_FILENAME = "model_metadata.json"

# Multi-model artifacts
ENSEMBLE_LR_FILENAME = "ensemble_lr.joblib"
ENSEMBLE_GBM_FILENAME = "ensemble_gbm.joblib"
KNOCKOUT_FILENAME = "knockout_model.joblib"
POISSON_HOME_FILENAME = "poisson_home.joblib"
POISSON_AWAY_FILENAME = "poisson_away.joblib"


def model_path() -> Path:
    return settings.MODEL_DIR / MODEL_FILENAME


def metadata_path() -> Path:
    return settings.MODEL_DIR / METADATA_FILENAME


def _path(name: str) -> Path:
    return settings.MODEL_DIR / name


def model_available() -> bool:
    return ensemble_available() or model_path().is_file()


def ensemble_available() -> bool:
    return _path(ENSEMBLE_LR_FILENAME).is_file() and _path(ENSEMBLE_GBM_FILENAME).is_file()


def knockout_available() -> bool:
    return _path(KNOCKOUT_FILENAME).is_file()


def poisson_available() -> bool:
    return _path(POISSON_HOME_FILENAME).is_file() and _path(POISSON_AWAY_FILENAME).is_file()


@lru_cache(maxsize=1)
def load_model():
    """Legacy logistic regression pipeline."""
    path = model_path()
    if not path.is_file():
        return None
    return joblib.load(path)


@lru_cache(maxsize=1)
def load_ensemble_lr():
    path = _path(ENSEMBLE_LR_FILENAME)
    return joblib.load(path) if path.is_file() else None


@lru_cache(maxsize=1)
def load_ensemble_gbm():
    path = _path(ENSEMBLE_GBM_FILENAME)
    return joblib.load(path) if path.is_file() else None


@lru_cache(maxsize=1)
def load_knockout_model():
    path = _path(KNOCKOUT_FILENAME)
    return joblib.load(path) if path.is_file() else None


@lru_cache(maxsize=1)
def load_poisson_home():
    path = _path(POISSON_HOME_FILENAME)
    return joblib.load(path) if path.is_file() else None


@lru_cache(maxsize=1)
def load_poisson_away():
    path = _path(POISSON_AWAY_FILENAME)
    return joblib.load(path) if path.is_file() else None


@lru_cache(maxsize=1)
def load_model_metadata() -> dict:
    path = metadata_path()
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def clear_cache() -> None:
    load_model.cache_clear()
    load_ensemble_lr.cache_clear()
    load_ensemble_gbm.cache_clear()
    load_knockout_model.cache_clear()
    load_poisson_home.cache_clear()
    load_poisson_away.cache_clear()
    load_model_metadata.cache_clear()


def save_model(pipeline, metadata: dict) -> tuple[Path, Path]:
    """Save legacy single model + metadata."""
    settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    mpath = model_path()
    metapath = metadata_path()
    joblib.dump(pipeline, mpath)
    with metapath.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    clear_cache()
    return mpath, metapath


def save_all_models(artifacts: dict[str, object], metadata: dict) -> Path:
    """Save ensemble, knockout, and Poisson models."""
    settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for filename, obj in artifacts.items():
        joblib.dump(obj, _path(filename))
    metapath = metadata_path()
    with metapath.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    clear_cache()
    return metapath
