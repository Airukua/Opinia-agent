from __future__ import annotations
import json
import os
from typing import Any, Dict
from utils.logger import get_logger
logger = get_logger(__name__)


def save_merged_output(payload: Dict[str, Any], output_path: str) -> None:
    """Writes merged evidence payload to disk as JSON.

    Args:
        payload: Full merged payload containing evidence and insights.
        output_path: Target JSON path for the merged payload.

    Example usage:
        >>> save_merged_output({"evidence": {}}, "outputs/merged.json")
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Merged evidence output saved: %s", output_path)


def save_split_outputs(
    *,
    evidence_snapshot: Dict[str, Any],
    llm_insights: Dict[str, Any],
    output_dir: str,
    evidence_filename: str,
    insights_filename: str,
) -> Dict[str, str]:
    """Writes evidence snapshot and viral LLM insights to separate JSON files.

    Args:
        evidence_snapshot: Evidence snapshot to persist.
        llm_insights: LLM insight payload to persist.
        output_dir: Directory to write the JSON outputs.
        evidence_filename: File name for the evidence snapshot output.
        insights_filename: File name for the LLM insight output.

    Returns:
        Dictionary with ``evidence`` and ``llm_insights`` output paths.

    Example usage:
        >>> result = save_split_outputs(
        ...     evidence_snapshot={"video": {}},
        ...     llm_insights={"available": False},
        ...     output_dir="outputs",
        ...     evidence_filename="evidence.json",
        ...     insights_filename="insights.json",
        ... )
        >>> "evidence" in result
        True
    """
    os.makedirs(output_dir, exist_ok=True)
    evidence_path = os.path.join(output_dir, evidence_filename)
    insights_path = os.path.join(output_dir, insights_filename)

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_snapshot, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Evidence snapshot saved: %s", evidence_path)

    with open(insights_path, "w", encoding="utf-8") as f:
        json.dump(llm_insights, f, ensure_ascii=False, indent=2, default=str)
    logger.info("Viral LLM insights saved: %s", insights_path)

    return {"evidence": evidence_path, "llm_insights": insights_path}
