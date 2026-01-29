"""JSON output utility for generating JSON artifacts alongside markdown."""

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def generate_json_output(artifact_type: str, data: Any, output_path: Path) -> Path:
    """Generate JSON output file for an artifact.

    Args:
        artifact_type: Type of artifact (story, epic, feature, report)
        data: Data to serialize (dict or Pydantic model)
        output_path: Path for JSON file (will replace .md with .json if needed)

    Returns:
        Path to generated JSON file
    """
    # Ensure .json extension
    if output_path.suffix == ".md":
        json_path = output_path.with_suffix(".json")
    elif output_path.suffix != ".json":
        json_path = output_path.with_suffix(".json")
    else:
        json_path = output_path

    # Convert Pydantic models to dict if needed
    if hasattr(data, "model_dump"):
        json_data = data.model_dump()
    elif hasattr(data, "dict"):
        json_data = data.dict()
    elif isinstance(data, dict):
        json_data = data
    else:
        json_data = {"data": str(data)}

    # Ensure directory exists
    json_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON file
    json_path.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    logger.info(
        "JSON output generated",
        artifact_type=artifact_type,
        path=str(json_path),
    )

    return json_path


def serialize_to_json(data: Any) -> str:
    """Serialize data to JSON string.

    Args:
        data: Data to serialize (dict, Pydantic model, or other)

    Returns:
        JSON string
    """
    if hasattr(data, "model_dump"):
        json_data = data.model_dump()
    elif hasattr(data, "dict"):
        json_data = data.dict()
    elif isinstance(data, dict):
        json_data = data
    else:
        json_data = {"data": str(data)}

    return json.dumps(json_data, indent=2, ensure_ascii=False)
