"""
Phase 8 — AI Correction Layer: Prediction Service
====================================================
Real-time inference module that loads the trained scikit-learn model
(from ``ml_models/ev_model.joblib``) and predicts ``ev_final`` from
a pre-match feature vector.

Cold-start fallback
--------------------
If the model file does **not** exist (e.g. before the first training run),
``predict_ev_final`` returns the raw ``ev_base`` verbatim.  This guarantees
the system never crashes due to a missing ML model.

Model caching
-------------
The model is loaded once from disk and held in a module-level cache so
subsequent calls do **not** re-read the file.  The cache persists for the
lifetime of the Python process.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_MODELS_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ml_models",
)
_MODEL_PATH: str = os.path.join(_MODELS_DIR, "ev_model.joblib")

# ---------------------------------------------------------------------------
# Feature schema
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
"""
Feature columns in the exact order expected by the trained model.
Must match ``train_ai_model.py`` / ``features_log`` column order.
"""

# ---------------------------------------------------------------------------
# In-memory model cache
# ---------------------------------------------------------------------------

_model_cache: Optional[object] = None
""":py:data:`None` until the first call to :func:`_load_model`."""


def _load_model() -> Optional[object]:
    """
    Load the trained model from disk, caching it in memory.

    Returns
    -------
    object or ``None``
        The deserialised scikit-learn estimator, or ``None`` if the file
        does not exist or failed to load.
    """
    global _model_cache

    if _model_cache is not None:
        return _model_cache

    if not os.path.isfile(_MODEL_PATH):
        logger.info("AI model not found at '%s' — cold start: returning ev_base.", _MODEL_PATH)
        return None

    try:
        _model_cache = joblib.load(_MODEL_PATH)
        logger.info("AI model loaded from '%s'", _MODEL_PATH)
        return _model_cache
    except Exception:
        logger.exception("Failed to load AI model from '%s'", _MODEL_PATH)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def predict_ev_final(features_dict: Dict[str, Any]) -> float:
    """
    Predict the AI-corrected expected value (``ev_final``).

    Parameters
    ----------
    features_dict : dict
        Feature vector with **all** of the following keys:

        - ``lambda_home``            — Poisson λ (home)
        - ``lambda_away``            — Poisson λ (away)
        - ``p_model``                — Model-estimated probability
        - ``p_book``                 — Margin-free bookmaker probability
        - ``ev_base``                — Raw expected value
        - ``team_strength_home``     — Home xG_diff (rolling)
        - ``team_strength_away``     — Away xG_diff (rolling)
        - ``stability_home``         — Home stability score
        - ``stability_away``         — Away stability score
        - ``odds``                   — Bookmaker decimal odds

    Returns
    -------
    float
        The predicted ``ev_final``.

        **Cold-start fallback** — if the model file does not exist, returns
        ``features_dict['ev_base']`` unchanged.  This prevents the betting
        pipeline from crashing before the first training run.

        **Error fallback** — if prediction fails for any reason (e.g. shape
        mismatch, NaN in input), also returns ``ev_base``.
    """
    model = _load_model()

    # ── Cold start: no model file yet ────────────────────────────────────
    if model is None:
        return float(features_dict.get("ev_base", 0.0))

    # ── Build feature array in the exact column order ────────────────────
    try:
        row: List[float] = []
        for col in FEATURE_COLUMNS:
            val = features_dict.get(col)
            row.append(float(val) if val is not None else 0.0)

        X = np.array([row])
    except Exception:
        logger.exception("Failed to assemble feature vector — falling back to ev_base")
        return float(features_dict.get("ev_base", 0.0))

    # ── Run inference ────────────────────────────────────────────────────
    try:
        prediction: float = float(model.predict(X)[0])
        return round(prediction, 6)
    except Exception:
        logger.exception("Model inference failed — falling back to ev_base")
        return float(features_dict.get("ev_base", 0.0))
