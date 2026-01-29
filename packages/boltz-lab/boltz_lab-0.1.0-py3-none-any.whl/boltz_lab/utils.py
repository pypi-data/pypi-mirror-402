"""Utility functions for Boltz Lab client."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import PredictionStatus


def extract_results_from_status(status: PredictionStatus) -> dict[str, Any] | None:
    """Extract results from a prediction status object.

    This handles both cases:
    1. Results embedded directly in prediction_results field
    2. Need to fetch from separate endpoint

    Args:
        status: PredictionStatus object

    Returns:
        Results dictionary if available, None otherwise
    """
    if status.prediction_results:
        return status.prediction_results
    return None


def save_results_to_file(results: dict[str, Any], filepath: str) -> None:
    """Save results dictionary to a JSON file.

    Args:
        results: Results dictionary to save
        filepath: Path to save the file
    """
    from pathlib import Path

    with Path(filepath).open("w") as f:
        json.dump(results, f, indent=2)


def format_results_summary(results: dict[str, Any]) -> str:
    """Format a summary of prediction results.

    Args:
        results: Results dictionary (prediction_results from API)

    Returns:
        Formatted summary string
    """
    summary_lines = [
        "Prediction Results Summary:",
        "-" * 40,
    ]

    if "status" in results:
        summary_lines.append(f"Status: {results['status']}")

    if "processing_time_ms" in results:
        summary_lines.append(f"Processing time: {results['processing_time_ms']}ms")

    # Add error info if failed
    if "error" in results and isinstance(results["error"], dict):
        summary_lines.append(f"Error: {results['error'].get('message', 'Unknown error')}")

    return "\n".join(summary_lines)
