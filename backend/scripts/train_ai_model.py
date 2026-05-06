"""
Phase 8 — ML Training Pipeline
================================
Standalone script that loads historical feature vectors from the
``features_log`` table, trains a ``HistGradientBoostingRegressor`` to
predict ``outcome_profit``, and persists the model to disk.

Usage (from the backend/ directory)::

    .\\venv312\\Scripts\\python.exe scripts\\train_ai_model.py

Exit codes
----------
0 — success (model trained and saved, OR not enough data)
1 — unexpected error
"""

import logging
import os
import sys
from typing import List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine, text

# Ensure the backend package is importable
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.core.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_ai_model")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FEATURE_COLUMNS: List[str] = [
    "lambda_home",
    "lambda_away",
    "p_model",
    "p_book",
    "ev_base",
    "team_strength_home",
    "team_strength_away",
    "stability_home",
    "stability_away",
    "odds",
]
"""Feature columns in the exact order expected by the model."""

TARGET_COLUMN: str = "outcome_profit"
"""Target variable — actual profit/loss after settlement."""

MODEL_DIR: str = os.path.join(_PROJECT_ROOT, "app", "ml_models")
MODEL_PATH: str = os.path.join(MODEL_DIR, "ev_model.joblib")

MIN_ROWS: int = 50
"""Minimum rows required before training. Below this, the script exits gracefully."""

TEST_SIZE: float = 0.2
RANDOM_STATE: int = 42


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_training_data(db_url: str) -> pd.DataFrame:
    """
    Load rows from ``features_log`` where ``outcome_profit IS NOT NULL``.

    Converts the async driver URI to a sync one (``+asyncpg`` → ``+psycopg2``)
    since this is a standalone script.

    If the table does not exist (fresh deployment) the function returns an
    empty DataFrame instead of crashing.
    """
    sync_url = db_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)

    query = text(f"""
        SELECT
            {', '.join(FEATURE_COLUMNS)},
            {TARGET_COLUMN}
        FROM features_log
        WHERE {TARGET_COLUMN} IS NOT NULL
    """)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
    except Exception as exc:
        logger.warning("Could not load training data: %s", exc)
        logger.warning("Returning empty DataFrame — training will be skipped.")
        df = pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN])
    finally:
        engine.dispose()

    return df


# ---------------------------------------------------------------------------
# Imputation
# ---------------------------------------------------------------------------


def impute_missing(X: pd.DataFrame) -> pd.DataFrame:
    """
    Fill NaN / None values with the column median.

    Operates on a copy to avoid mutating the caller's DataFrame.
    """
    df = X.copy()
    for col in df.columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            median_val = df[col].median()
            if pd.isna(median_val):
                median_val = 0.0
            df[col] = df[col].fillna(median_val)
            logger.info(
                "Imputed column '%s': %d null values → %.4f",
                col, null_count, median_val,
            )
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Orchestrate training: load → impute → split → fit → evaluate → save."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    db_url: str = settings.SQLALCHEMY_DATABASE_URI
    logger.info("Loading training data from features_log...")
    df = load_training_data(db_url)

    n_rows = len(df)
    logger.info("Loaded %d rows with non-null outcome_profit.", n_rows)

    if n_rows < MIN_ROWS:
        logger.warning(
            "Not enough data to train (%d < %d). Exiting.",
            n_rows, MIN_ROWS,
        )
        return  # graceful exit — no model saved

    # ── Separate features & target ───────────────────────────────────────
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    # ── Impute missing values ────────────────────────────────────────────
    X = impute_missing(X)

    logger.info("Feature matrix shape: %s", X.shape)

    # ── Train / test split ───────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    logger.info(
        "Split: %d train / %d test rows",
        len(X_train), len(X_test),
    )

    # ── Train model ──────────────────────────────────────────────────────
    model = HistGradientBoostingRegressor(
        random_state=RANDOM_STATE,
        max_iter=300,
        learning_rate=0.1,
        max_depth=5,
        min_samples_leaf=5,
        validation_fraction=0.1,
        n_iter_no_change=15,
        early_stopping=True,
    )
    model.fit(X_train, y_train)

    # ── Evaluate ─────────────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    logger.info("=" * 50)
    logger.info("EVALUATION METRICS (test set)")
    logger.info("  MSE: %.6f", mse)
    logger.info("  MAE: %.6f", mae)
    logger.info("  RMSE: %.6f", np.sqrt(mse))

    # Feature importances
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    logger.info("Feature importances (descending):")
    for rank, idx in enumerate(sorted_idx, start=1):
        logger.info("  %2d. %-22s  %.4f", rank, FEATURE_COLUMNS[idx], importances[idx])

    logger.info("=" * 50)

    # ── Save model ───────────────────────────────────────────────────────
    joblib.dump(model, MODEL_PATH)
    logger.info("Model saved to %s", MODEL_PATH)
    logger.info("Training pipeline complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Fatal error in training pipeline")
        sys.exit(1)
