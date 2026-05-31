"""
YOLOv8 classification model wrapper for tobacco leaf disease detection.

Loads a trained YOLOv8 classification model and provides a prediction
interface that returns the top disease class, confidence score, and
ranked list of all class probabilities.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PIL import Image
import io

logger = logging.getLogger(__name__)

# ── Class mapping (matches training label order) ────────────────────────
CLASS_MAP: dict[int, str] = {
    0: "Alternaria Alternata",
    1: "Cercospora Nicotianae",
    2: "Healthy",
}

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "best.pt"

# ── Lazy-loaded singleton ───────────────────────────────────────────────
_model = None


def _load_model():
    """Load the YOLO model once and cache it as a module-level singleton."""
    global _model
    if _model is not None:
        return _model

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. "
            "Please place your trained best.pt in the models/ directory."
        )

    try:
        from ultralytics import YOLO

        _model = YOLO(str(MODEL_PATH))
        logger.info("YOLOv8 classification model loaded from %s", MODEL_PATH)
        return _model
    except Exception as exc:
        logger.error("Failed to load YOLO model: %s", exc)
        raise RuntimeError(f"Could not load classification model: {exc}") from exc


def predict(image_bytes: bytes) -> dict[str, Any]:
    """
    Run inference on raw image bytes.

    Parameters
    ----------
    image_bytes : bytes
        Raw bytes of a JPEG / PNG / WebP image.

    Returns
    -------
    dict
        {
            "class_name":       str,   # predicted class label
            "confidence":       float, # probability of the top class (0-1)
            "top_predictions":  list[dict]  # all classes ranked by probability
        }

    Raises
    ------
    FileNotFoundError
        If the model weights file is missing.
    RuntimeError
        If model loading or inference fails.
    ValueError
        If the image cannot be decoded.
    """
    model = _load_model()

    # Decode & Enhance image ──────────────────────────────────────────────
    try:
        from PIL import ImageOps
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # Apply Auto-orientation (EXIF-stripping)
        image = ImageOps.exif_transpose(image)
        # Apply Stretch resize to 640x640 exactly as done in training
        image = image.resize((640, 640), Image.Resampling.BILINEAR)
    except Exception as exc:
        raise ValueError(f"Unable to decode the uploaded image: {exc}") from exc

    # Run inference ───────────────────────────────────────────────────────
    try:
        results = model(image, verbose=False)
    except Exception as exc:
        raise RuntimeError(f"Model inference failed: {exc}") from exc

    # Parse results ───────────────────────────────────────────────────────
    result = results[0]
    probs = result.probs

    # Top-1 prediction
    top_idx = int(probs.top1)
    top_conf = float(probs.top1conf)
    class_name = CLASS_MAP.get(top_idx, f"Unknown ({top_idx})")

    # Full ranked list
    all_probs = probs.data.tolist()
    top_predictions = sorted(
        [
            {
                "class_name": CLASS_MAP.get(i, f"Unknown ({i})"),
                "confidence": round(float(p), 4),
            }
            for i, p in enumerate(all_probs)
        ],
        key=lambda x: x["confidence"],
        reverse=True,
    )

    return {
        "class_name": class_name,
        "confidence": round(top_conf, 4),
        "top_predictions": top_predictions,
    }
