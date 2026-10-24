"""Evaluation helpers for model-vs-human validation tracking."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import sqrt
from typing import Any, Dict, List, Optional


@dataclass
class EvaluationRecord:
    """Single benchmark record for one resume assessment."""

    resume_name: str
    model_score: int
    human_score: int
    notes: str = ""
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if not payload["created_at"]:
            payload["created_at"] = (
                datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            )
        payload["absolute_error"] = abs(int(payload["model_score"]) - int(payload["human_score"]))
        return payload


def _pearson_correlation(xs: List[float], ys: List[float]) -> Optional[float]:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = sqrt(sum((y - mean_y) ** 2 for y in ys))
    den = den_x * den_y
    if den == 0:
        return None
    return num / den


def _normalize_score(value: Any) -> int:
    """Normalize arbitrary score-like input to an integer in the range 0-100."""
    try:
        score = int(float(value))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, score))


def build_evaluation_record(
    resume_name: str,
    model_score: int,
    human_score: int,
    notes: str = "",
) -> Dict[str, Any]:
    """Create a normalized evaluation record dict."""
    record = EvaluationRecord(
        resume_name=str(resume_name or "resume"),
        model_score=_normalize_score(model_score),
        human_score=_normalize_score(human_score),
        notes=str(notes or "").strip(),
    )
    return record.to_dict()


def summarize_evaluation(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute aggregate evaluation metrics over benchmark records."""
    valid_records: List[Dict[str, Any]] = []
    for record in records or []:
        try:
            model = float(record.get("model_score", ""))
            human = float(record.get("human_score", ""))
        except (TypeError, ValueError):
            continue
        valid_records.append({"model_score": model, "human_score": human})

    n = len(valid_records)
    if n == 0:
        return {
            "count": 0,
            "mae": None,
            "rmse": None,
            "correlation": None,
        }

    errors = [abs(r["model_score"] - r["human_score"]) for r in valid_records]
    squared_errors = [(r["model_score"] - r["human_score"]) ** 2 for r in valid_records]
    mae = sum(errors) / n
    rmse = sqrt(sum(squared_errors) / n)

    xs = [r["model_score"] for r in valid_records]
    ys = [r["human_score"] for r in valid_records]
    corr = _pearson_correlation(xs, ys)

    return {
        "count": n,
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "correlation": None if corr is None else round(corr, 4),
    }
