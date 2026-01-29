"""Main client for Boltz Lab API."""

import asyncio
import json
import logging
import os
import sys
import webbrowser
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import yaml
from dotenv import load_dotenv
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import get_config
from .exceptions import (
    BoltzAPIError,
    BoltzAuthenticationError,
    BoltzConnectionError,
    BoltzNotFoundError,
    BoltzTimeoutError,
    BoltzValidationError,
)
from .models import (
    JobStatus,
    PredictionJob,
    PredictionListResponse,
    PredictionOutputResponse,
    PredictionStatus,
    SubmitPredictionRequest,
    SubmitPredictionResponse,
)
from .prediction_flags import Flags
from .prediction_flags import convert_to_api as convert_prediction_flags_to_api

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables (can be disabled for testing)
if os.getenv("DISABLE_DOTENV") != "1":
    load_dotenv()


def is_retriable_http_error(exception: Exception) -> bool:
    """Check if an HTTP error should be retried."""
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on server errors and specific client errors
        status_code = exception.response.status_code
        return status_code in {408, 429} or (500 <= status_code < 600)

    # After mapping, our custom exceptions preserve status_code on BoltzAPIError
    if isinstance(exception, (BoltzTimeoutError, BoltzConnectionError)):
        return True
    if isinstance(exception, BoltzAPIError) and getattr(exception, "status_code", None) is not None:
        status_code = exception.status_code  # type: ignore[assignment]
        return (status_code in {408, 429}) or (500 <= int(status_code) < 600)

    return False


def log_retry_attempt(retry_state: RetryCallState) -> None:
    """Log retry attempts with user-friendly messages."""
    if retry_state.attempt_number > 1:
        wait_time = retry_state.next_action.sleep if retry_state.next_action else 0
        logger.info(f"⚠️  Connection attempt {retry_state.attempt_number} of 3 failed. Retrying in {wait_time:.0f} seconds...")
        if retry_state.attempt_number == 2:
            logger.info("💡 Tip: If using localhost, ensure the server is running")


DEFAULT_RETRY_HTTP_CONNECTION = retry(
    retry=(retry_if_exception_type(httpx.TransportError) | retry_if_exception(is_retriable_http_error)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=log_retry_attempt,
    reraise=True,
)


def _prompt_for_api_key(signup_url: str) -> str | None:
    """Prompt user for API key interactively.

    Args:
        signup_url: Signup URL to show in prompt

    Returns:
        API key if provided and valid, None if user declined or invalid
    """
    # Check if we're in an interactive terminal
    if not sys.stdin.isatty():
        return None

    print("\n" + "=" * 60)
    print("No API key found!")
    print("=" * 60)
    print("\nTo use Boltz Lab, you need an API key.")
    print(f"Get one at: {signup_url}?intent=open-api-key-settings")
    print()

    # Offer to open browser
    try:
        open_browser = input("Would you like to open this URL in your browser? (y/N): ").strip().lower()
        if open_browser in ["y", "yes"]:
            print("Opening browser...")
            webbrowser.open(f"{signup_url}?intent=open-api-key-settings")
    except (KeyboardInterrupt, EOFError):
        print("\n")

    print("\nExample format: sk-...")
    print()

    try:
        api_key = input("Enter your API key (or press Enter to skip): ").strip()

        if not api_key:
            print("Skipping API key setup.")
            return None

        return api_key

    except (KeyboardInterrupt, EOFError):
        print("\n\nAPI key setup cancelled.")
        return None


class BoltzLabClient:
    """Async client for Boltz Lab API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        signup_url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the client.

        Args:
            api_key: API key for authentication. If not provided, checks BOLTZ_API_KEY env var, then config file.
            base_url: Base URL for the API. If not provided, checks BOLTZ_API_ENDPOINT env var, then config file.
            signup_url: Signup URL for getting API key. If not provided, checks BOLTZ_SIGNUP_URL env var, then config file.
            timeout: Default timeout for requests in seconds.

        Priority order:
            1. Direct parameter
            2. Environment variable
            3. Config file (~/.config/boltz-lab/config.json)
            4. Default value (for base_url and signup_url only)
        """
        config = get_config()

        # Default to production URL, but allow override
        default_url = "https://lab.boltz.bio"

        # Load base_url with priority: parameter > env > config > default
        self.base_url = base_url or os.getenv("BOLTZ_API_ENDPOINT") or config.get_endpoint() or default_url
        if self.base_url:
            self.base_url = self.base_url.rstrip("/")

        # Load signup_url with priority: parameter > env > config > default
        self.signup_url = signup_url or os.getenv("BOLTZ_SIGNUP_URL") or config.get_signup_url() or default_url
        if self.signup_url:
            self.signup_url = self.signup_url.rstrip("/")

        # Load api_key with priority: parameter > env > config
        self.api_key = api_key or os.getenv("BOLTZ_API_KEY") or config.get_api_key()

        if not self.api_key:
            # Try interactive prompt if in TTY
            prompted_key = _prompt_for_api_key(self.signup_url)

            if prompted_key:
                # Save to config for future use
                config.save_config(api_key=prompted_key)
                self.api_key = prompted_key
                print(f"✓ API key saved to {config.config_path}")
            else:
                # Non-interactive or user declined
                config_path = config.config_path
                print(
                    "\nAPI key must be provided via one of:\n"
                    "  1. Direct parameter\n"
                    "  2. BOLTZ_API_KEY environment variable\n"
                    f"  3. Config file at {config_path}\n\n"
                    f"To get an API key, please visit {self.signup_url}?intent=open-api-key-settings and sign up for an account.\n\n"
                    "To save your API key in the config file, run:\n"
                    "  boltz-lab config --api-key YOUR_API_KEY"
                )
                sys.exit(1)

        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            # Configure timeouts: connect timeout of 10s, read timeout of configured value
            timeout_config = httpx.Timeout(
                timeout=self.timeout,  # Total timeout
                connect=10.0,  # Connection timeout
                read=self.timeout,  # Read timeout
                write=30.0,  # Write timeout
                pool=None,  # No pool timeout
            )

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=timeout_config,
            )
        return self._client

    async def __aenter__(self) -> "BoltzLabClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @DEFAULT_RETRY_HTTP_CONNECTION
    async def _stream_download_with_retries(
        self,
        url: str,
        output_file: Path,
        timeout: float | httpx.Timeout | None = None,
    ) -> None:
        """Stream a download from a URL to a file with retries."""
        timeout_value = timeout or httpx.Timeout(300.0)
        async with httpx.AsyncClient(timeout=timeout_value) as download_client, download_client.stream("GET", url) as response:
            response.raise_for_status()

            total_size = response.headers.get("content-length")
            if total_size:
                logger.info(f"Download size: {int(total_size) / 1024 / 1024:.2f} MB")

            with output_file.open("wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)

    def _handle_response_error(self, response: httpx.Response):
        """Handle HTTP error responses."""
        # Include parsed JSON when available; otherwise include a brief text preview
        response_data = None
        if response.content:
            try:
                response_data = response.json()
            except Exception:
                response_data = {"text": response.text[:1000]}

        if response.status_code == 401:
            raise BoltzAuthenticationError(
                "Authentication failed. Check your API key.",
                status_code=response.status_code,
                response_data=response_data,
            )
        if response.status_code == 404:
            raise BoltzNotFoundError(
                "Resource not found",
                status_code=response.status_code,
                response_data=response_data,
            )
        if response.status_code == 400:
            raise BoltzValidationError(
                "Invalid request",
                status_code=response.status_code,
                response_data=response_data,
            )
        raise BoltzAPIError(
            f"API request failed: {response.status_code}",
            status_code=response.status_code,
            response_data=response_data,
        )

    @DEFAULT_RETRY_HTTP_CONNECTION
    async def _make_request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic."""
        url = f"/api/v1/connect/predictions{path}"

        logger.debug(f"Making {method} request to: {self.base_url}{url}")
        if "json" in kwargs:
            logger.debug(f"Request body: {json.dumps(kwargs['json'], indent=2)}")
        if "params" in kwargs:
            logger.debug(f"Request params: {kwargs['params']}")

        try:
            response = await self.client.request(method, url, **kwargs)
            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            logger.debug(f"Request timeout: {str(e)}")
            raise BoltzTimeoutError(f"Request timed out: {str(e)}") from e
        except httpx.ConnectError as e:
            logger.debug(f"Connection failed: {str(e)}")
            raise BoltzConnectionError(
                f"Failed to connect to API server at {self.base_url}. Please check your internet connection and API endpoint."
            ) from e
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code if e.response is not None else None
            body_preview = None
            try:
                body_preview = e.response.text if e.response is not None else None
            except Exception:
                body_preview = None

            logger.error(f"HTTP error {status_code}: {body_preview}")
            self._handle_response_error(e.response)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in _make_request: {type(e).__name__}: {str(e)}")
            raise

    async def submit_prediction(
        self,
        complex_data: dict[str, Any],
        prediction_name: str | None = None,
        flags: Flags | None = None,
    ) -> PredictionJob:
        """Submit a prediction job.

        Args:
            complex_data: The complex data for prediction (with sequences, constraints, properties)
            prediction_name: Optional name for the prediction
            flags: Optional dictionary of prediction flags

        Returns:
            PredictionJob object for tracking the submission
        """
        # prediction_inputs wraps complex_data in inference_input
        inputs_data: dict[str, Any] = {
            "inference_input": complex_data,
        }

        # Add flags as inference_options if provided
        if flags:
            inputs_data["inference_options"] = convert_prediction_flags_to_api(flags)

        request_data = SubmitPredictionRequest(prediction_name=prediction_name, prediction_inputs=inputs_data)
        logger.debug(f"Request data: {request_data}")

        request_json = request_data.model_dump(exclude_none=True)

        response = await self._make_request(
            "POST",
            "/boltz2",
            json=request_json,
        )

        result = SubmitPredictionResponse(**response.json())
        return PredictionJob(result.prediction_id, self)

    async def submit_job_from_yaml(
        self,
        yaml_path: str,
        prediction_name: str | None = None,
        flags: Flags | None = None,
    ) -> PredictionJob:
        """Submit a prediction job from a YAML file or URL.

        Args:
            yaml_path: Path to YAML file or HTTP/HTTPS URL containing job specification
            prediction_name: Optional name for the prediction
            flags: Optional dictionary of prediction flags

        Returns:
            PredictionJob object for tracking the submission
        """
        # Check if it's a URL
        if yaml_path.startswith(("http://", "https://")):
            logger.debug(f"Fetching YAML from URL: {yaml_path}")
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(yaml_path)
                    response.raise_for_status()
                    data = yaml.safe_load(response.text)
            except httpx.ConnectError as e:
                raise BoltzConnectionError(f"Failed to fetch YAML from URL: {yaml_path}") from e
            except httpx.TimeoutException as e:
                raise BoltzTimeoutError(f"Timeout while fetching YAML from URL: {yaml_path}") from e
            except httpx.HTTPStatusError as e:
                raise BoltzAPIError(f"HTTP error {e.response.status_code} while fetching YAML from URL: {yaml_path}") from e
            except yaml.YAMLError as e:
                raise BoltzValidationError(f"Invalid YAML format in URL content: {str(e)}") from e
        else:
            # Local file
            with Path(yaml_path).open("r") as f:
                data = yaml.safe_load(f)

        # Basic validation - just check structure exists
        if not isinstance(data, dict):
            raise ValueError("Invalid YAML format")

        return await self.submit_job_from_dict(
            job_data=data,
            prediction_name=prediction_name,
            flags=flags,
        )

    async def submit_job_from_dict(
        self,
        job_data: dict[str, Any],
        prediction_name: str | None = None,
        flags: Flags | None = None,
    ) -> PredictionJob:
        """Submit a prediction job from a dictionary.

        Args:
            job_data: Dictionary containing job specification
            prediction_name: Optional name for the prediction
            flags: Optional dictionary of prediction flags

        Returns:
            PredictionJob object for tracking the submission
        """
        return await self.submit_prediction(
            complex_data=job_data,
            prediction_name=prediction_name,
            flags=flags,
        )

    async def get_prediction_status(self, prediction_id: str) -> PredictionStatus:
        """Get the status of a prediction.

        Args:
            prediction_id: The prediction ID to check

        Returns:
            PredictionStatus object with current status
        """
        logger.debug(f"Requesting status for prediction: {prediction_id}")

        response = await self._make_request("GET", f"/{prediction_id}")
        response_data = response.json()

        logger.debug(f"Status response: {json.dumps(response_data, indent=2)}")

        status = PredictionStatus(**response_data)

        # Check if results are available directly in the response
        if status.prediction_results:
            logger.debug(f"Results data: {json.dumps(status.prediction_results, indent=2)}")

        return status

    async def list_predictions(
        self,
        status: JobStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PredictionListResponse:
        """List predictions with optional filtering.

        Args:
            status: Optional status filter
            limit: Maximum number of results (1-100)
            offset: Offset for pagination

        Returns:
            PredictionListResponse with list of predictions
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        if status:
            params["status"] = status.value

        response = await self._make_request("GET", "", params=params)
        return PredictionListResponse(**response.json())

    async def get_prediction_output_url(self, prediction_id: str) -> PredictionOutputResponse:
        """Get download URL for prediction results.

        Args:
            prediction_id: The prediction ID

        Returns:
            PredictionOutputResponse with download URL and expiry
        """
        logger.debug(f"Requesting output URL for prediction: {prediction_id}")

        try:
            response = await self._make_request("GET", f"/{prediction_id}/output")
            response_data = response.json()

            logger.debug(f"Output URL response status: {response.status_code}")
            logger.debug(f"Output URL response headers: {dict(response.headers)}")
            logger.debug(f"Output URL response data: {json.dumps(response_data, indent=2)}")

            return PredictionOutputResponse(**response_data)
        except Exception as e:
            logger.error(f"Error getting output URL: {type(e).__name__}: {str(e)}")
            if hasattr(e, "response") and hasattr(e.response, "text"):
                logger.error(f"Response body: {e.response.text}")
            raise

    async def download_results(
        self, prediction_id: str, output_dir: str = ".", output_format: str = "archive", output_filename: str | None = None
    ) -> str:
        """Download prediction results to a local file.

        Args:
            prediction_id: The prediction ID
            output_dir: Directory to save the results
            output_format: Format to download ('archive' or 'json')
            output_filename: Optional custom filename (without extension)

        Returns:
            Path to the downloaded file
        """
        # Create output directory if needed
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Get the prediction status
        logger.info(f"Fetching prediction status for format: {output_format}")
        status = await self.get_prediction_status(prediction_id)

        if output_format == "json":
            # Download JSON format from prediction_results
            if not status.prediction_results:
                raise BoltzAPIError("No JSON results available for this prediction")

            filename = output_filename or status.prediction_name
            output_file = output_path / f"{filename}.json"

            logger.info("Saving results as JSON...")
            output_file.write_text(json.dumps(status.prediction_results, indent=2))
            logger.info(f"Results saved to: {output_file}")
            return str(output_file)

        if output_format == "archive":
            # Download archive (tar.gz) format from download_url
            if not status.prediction_results or not isinstance(status.prediction_results, dict):
                raise BoltzAPIError("No results available for this prediction")

            # Extract the download_url from the prediction results
            results_file_url = None
            if (
                "status" in status.prediction_results
                and status.prediction_results["status"] == "completed"
                and "output" in status.prediction_results
                and "download_url" in status.prediction_results["output"]
            ):
                results_file_url = status.prediction_results["output"]["download_url"]
            if not results_file_url:
                raise BoltzAPIError("No tar.gz archive URL available for this prediction")

            # Determine filename
            filename = output_filename or status.prediction_name
            output_file = output_path / f"{filename}.tar.gz"

            # Download the file with retries
            await self._stream_download_with_retries(
                results_file_url,
                output_file,
                timeout=httpx.Timeout(300.0),
            )
            logger.info(f"Archive downloaded to: {output_file}")

            return str(output_file)

        raise ValueError(f"Invalid output format: {output_format}. Must be 'archive' or 'json'.")

    async def wait_for_prediction(
        self,
        prediction_id: str,
        polling_interval: int = 5,
        timeout: int | None = None,
        progress_callback: Callable[[PredictionStatus], None] | None = None,
    ) -> PredictionStatus:
        """Wait for a prediction to complete.

        Args:
            prediction_id: The prediction ID to wait for
            polling_interval: Seconds between status checks
            timeout: Maximum seconds to wait (None for no timeout)
            progress_callback: Optional callback for status updates

        Returns:
            Final PredictionStatus when job completes

        Raises:
            BoltzTimeoutError: If timeout is exceeded
            BoltzAPIError: If job fails
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            status = await self.get_prediction_status(prediction_id)

            if progress_callback:
                progress_callback(status)

            # Check terminal states
            if status.prediction_status == JobStatus.COMPLETED.value:
                return status
            if status.prediction_status in [
                JobStatus.FAILED.value,
                JobStatus.CANCELLED.value,
                JobStatus.TIMED_OUT.value,
            ]:
                raise BoltzAPIError(f"Prediction failed with status: {status.prediction_status}")

            # Check timeout
            if timeout and (asyncio.get_event_loop().time() - start_time) > timeout:
                raise BoltzTimeoutError(f"Prediction did not complete within {timeout} seconds")

            # Wait before next check
            await asyncio.sleep(polling_interval)
