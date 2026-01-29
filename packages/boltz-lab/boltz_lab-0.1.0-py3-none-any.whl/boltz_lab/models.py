"""Data models for Boltz Lab API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from .client import BoltzLabClient


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "PENDING"
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


# API request/response models
class SubmitPredictionRequest(BaseModel):
    """Request model for submitting a prediction."""

    prediction_name: str | None = None
    prediction_inputs: dict[str, Any]


class SubmitPredictionResponse(BaseModel):
    """Response model for job submission."""

    prediction_id: str
    message: str


class PredictionStatus(BaseModel):
    """Prediction status response model."""

    prediction_id: str
    prediction_name: str
    prediction_type: str
    prediction_status: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    prediction_results: dict[str, Any] | None = None


class PredictionListResponse(BaseModel):
    """Response model for listing predictions."""

    predictions: list[PredictionStatus]
    total: int


class PredictionOutputResponse(BaseModel):
    """Response model for getting prediction output URL."""

    download_url: str
    expires_in: int


class PredictionJob:
    """Represents a submitted prediction job."""

    def __init__(self, prediction_id: str, client: BoltzLabClient):
        self.prediction_id = prediction_id
        self._client = client

    async def get_status(self) -> PredictionStatus:
        """Get current status of the job."""
        return await self._client.get_prediction_status(self.prediction_id)

    async def wait_for_completion(
        self,
        polling_interval: int = 5,
        timeout: int | None = None,
        progress_callback: Any | None = None,
    ) -> PredictionStatus:
        """Wait for job to complete, polling at the specified interval."""
        return await self._client.wait_for_prediction(
            self.prediction_id,
            polling_interval=polling_interval,
            timeout=timeout,
            progress_callback=progress_callback,
        )

    async def download_results(self, output_dir: str = ".", output_format: str = "archive", output_filename: str | None = None) -> str:
        """Download job results to specified directory.

        Args:
            output_dir: Directory to save the results
            output_format: Format to download ('archive' or 'json')
            output_filename: Optional custom filename (without extension)

        Returns:
            Path to the downloaded file
        """
        return await self._client.download_results(self.prediction_id, output_dir, output_format=output_format, output_filename=output_filename)

    def __repr__(self) -> str:
        return f"PredictionJob(prediction_id='{self.prediction_id}')"
