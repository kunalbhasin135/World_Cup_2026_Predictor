#!/usr/bin/env python3
"""
Train ensemble outcome models, knockout binary model, and Poisson score models.

Usage (from backend/):
    python scripts/train_model.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.metrics import accuracy_score, brier_score_loss, classification_report, log_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.services.ml.feature_vector import FEATURE_NAMES
from app.services.ml.model_loader import (
    ENSEMBLE_GBM_FILENAME,
    ENSEMBLE_LR_FILENAME,
    KNOCKOUT_FILENAME,
    POISSON_AWAY_FILENAME,
    POISSON_HOME_FILENAME,
    save_all_models,
    save_model,
)
from app.services.ml.training_dataset import (
    build_knockout_dataset,
    build_training_dataset,
    dataset_summary,
)


def _multiclass_brier(y_true: np.ndarray, proba: np.ndarray) -> float:
    """Mean one-vs-rest Brier score across classes."""
    scores = []
    for cls in range(proba.shape[1]):
        binary = (y_true == cls).astype(int)
        scores.append(brier_score_loss(binary, proba[:, cls]))
    return float(np.mean(scores))


def main() -> None:
    print("Building point-in-time training dataset (matches since 2000)...")
    X, y, weights, y_home, y_away = build_training_dataset(min_year=2000, min_team_matches=10)
    summary = dataset_summary(y)
    print(f"Samples: {summary['total_samples']:,}")
    print(
        f"Class balance — home win: {summary['home_win_pct']}%, "
        f"draw: {summary['draw_pct']}%, away win: {summary['away_win_pct']}%"
    )

    X_train, X_test, y_train, y_test, w_train, w_test = train_test_split(
        X, y, weights, test_size=0.2, random_state=42, stratify=y
    )
    _, _, y_home_train, y_home_test = train_test_split(
        X, y_home, test_size=0.2, random_state=42, stratify=y
    )
    _, _, y_away_train, y_away_test = train_test_split(
        X, y_away, test_size=0.2, random_state=42, stratify=y
    )

    lr_base = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    solver="lbfgs",
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    print("Training calibrated logistic regression...")
    lr_calibrated = CalibratedClassifierCV(lr_base, method="isotonic", cv=3)
    lr_calibrated.fit(X_train, y_train, sample_weight=w_train)

    print("Training gradient boosting classifier...")
    gbm = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.08,
        max_depth=6,
        random_state=42,
    )
    gbm.fit(X_train, y_train, sample_weight=w_train)

    lr_proba = lr_calibrated.predict_proba(X_test)
    gbm_proba = gbm.predict_proba(X_test)
    ensemble_proba = 0.45 * lr_proba + 0.55 * gbm_proba
    ensemble_pred = ensemble_proba.argmax(axis=1)

    accuracy = accuracy_score(y_test, ensemble_pred)
    ll = log_loss(y_test, ensemble_proba)
    brier = _multiclass_brier(y_test, ensemble_proba)

    print(f"Ensemble test accuracy: {accuracy:.3f}")
    print(f"Log loss: {ll:.4f} | Brier (mean OVR): {brier:.4f}")
    print(classification_report(y_test, ensemble_pred, target_names=["home_win", "draw", "away_win"]))

    # Knockout binary model (no draws)
    print("\nTraining knockout binary model...")
    X_ko, y_ko, w_ko = build_knockout_dataset(min_year=2000, min_team_matches=10)
    X_ko_train, X_ko_test, y_ko_train, y_ko_test, w_ko_train, _ = train_test_split(
        X_ko, y_ko, w_ko, test_size=0.2, random_state=42, stratify=y_ko
    )
    ko_pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    solver="lbfgs",
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    ko_pipeline.fit(X_ko_train, y_ko_train, clf__sample_weight=w_ko_train)
    ko_acc = accuracy_score(y_ko_test, ko_pipeline.predict(X_ko_test))
    print(f"Knockout model accuracy: {ko_acc:.3f}")

    # Poisson score models
    print("\nTraining Poisson goal models...")
    poisson_home = Pipeline([("scaler", StandardScaler()), ("reg", PoissonRegressor(max_iter=500))])
    poisson_away = Pipeline([("scaler", StandardScaler()), ("reg", PoissonRegressor(max_iter=500))])
    poisson_home.fit(X_train, y_home_train, reg__sample_weight=w_train)
    poisson_away.fit(X_train, y_away_train, reg__sample_weight=w_train)
    home_mae = np.mean(np.abs(poisson_home.predict(X_test) - y_home_test))
    away_mae = np.mean(np.abs(poisson_away.predict(X_test) - y_away_test))
    print(f"Poisson MAE — home: {home_mae:.3f}, away: {away_mae:.3f}")

    metadata = {
        "model_type": "ensemble_lr_gbm",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_names": FEATURE_NAMES,
        "class_labels": {"0": "team_a_win", "1": "draw", "2": "team_b_win"},
        "ensemble_weights": {"logistic_regression": 0.45, "gradient_boosting": 0.55},
        "training_samples": int(len(y_train)),
        "test_samples": int(len(y_test)),
        "test_accuracy": round(float(accuracy), 4),
        "log_loss": round(float(ll), 4),
        "brier_score": round(float(brier), 4),
        "knockout_accuracy": round(float(ko_acc), 4),
        "poisson_home_mae": round(float(home_mae), 4),
        "poisson_away_mae": round(float(away_mae), 4),
        "dataset_summary": summary,
    }

    save_all_models(
        {
            ENSEMBLE_LR_FILENAME: lr_calibrated,
            ENSEMBLE_GBM_FILENAME: gbm,
            KNOCKOUT_FILENAME: ko_pipeline,
            POISSON_HOME_FILENAME: poisson_home,
            POISSON_AWAY_FILENAME: poisson_away,
        },
        metadata,
    )

    # Keep legacy single-file model for backward compatibility
    save_model(lr_calibrated, metadata)
    print("\nSaved ensemble, knockout, and Poisson models.")
    print("Done. Restart the API to serve updated predictions.")


if __name__ == "__main__":
    main()
