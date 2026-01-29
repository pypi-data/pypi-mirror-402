"""Tests for the Boltz Lab API client."""

import asyncio
import json
from pathlib import Path

import pytest

from boltz_lab import (
    BoltzAuthenticationError,
    BoltzLabClient,
    PredictionJob,
    PredictionStatus,
)


@pytest.fixture
def sample_yaml_file(tmp_path, yaml_content):
    """Create a sample YAML file for testing."""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text(yaml_content)
    return str(yaml_file)


class TestBoltzLabClient:
    """Test cases for BoltzLabClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initialization with API key."""
        assert client.api_key == "test-key"
        assert client.base_url == "https://lab.boltz.bio"

    @pytest.mark.asyncio
    async def test_client_initialization_from_env(self, monkeypatch):
        """Test client initialization from environment variables."""
        monkeypatch.setenv("BOLTZ_API_KEY", "env-test-key")
        monkeypatch.setenv("BOLTZ_API_ENDPOINT", "https://test.api.boltz.com")

        client = BoltzLabClient()
        assert client.api_key == "env-test-key"
        assert client.base_url == "https://test.api.boltz.com"
        await client.close()

    def test_client_initialization_no_api_key(self, monkeypatch):
        """Test client initialization exits without API key."""
        from unittest.mock import MagicMock

        # Mock sys.exit to prevent actual exit
        mock_exit = MagicMock()
        monkeypatch.setattr("sys.exit", mock_exit)

        # Mock print to suppress output
        mock_print = MagicMock()
        monkeypatch.setattr("builtins.print", mock_print)

        # Should call sys.exit(1)
        BoltzLabClient(base_url="https://lab.boltz.bio")

        mock_exit.assert_called_once_with(1)

    def test_client_initialization_with_interactive_prompt_valid_key(self, monkeypatch, tmp_path):
        """Test client initialization with interactive prompt accepting key."""
        from unittest.mock import MagicMock

        from boltz_lab.config import reset_config

        # Use tmp config directory - must set BEFORE resetting config
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        # Reset config to use new directory
        reset_config()

        # Mock TTY check to return True (interactive)
        mock_isatty = MagicMock(return_value=True)
        monkeypatch.setattr("sys.stdin.isatty", mock_isatty)

        # Mock input to return API key
        mock_input = MagicMock(return_value="test-prompted-key")
        monkeypatch.setattr("builtins.input", mock_input)

        # Mock print to suppress output
        mock_print = MagicMock()
        monkeypatch.setattr("builtins.print", mock_print)

        # Initialize client - should prompt and save
        client = BoltzLabClient(base_url="https://lab.boltz.bio")

        assert client.api_key == "test-prompted-key"
        assert mock_input.called
        assert mock_print.called

        # Verify key was saved
        config_file = tmp_path / "boltz-lab" / "config.json"
        assert config_file.exists()
        saved_config = json.loads(config_file.read_text())
        assert saved_config["api_key"] == "test-prompted-key"

    def test_client_initialization_with_interactive_prompt_empty_input(self, monkeypatch):
        """Test client initialization with interactive prompt rejecting (empty input)."""
        from unittest.mock import MagicMock

        # Mock TTY check
        mock_isatty = MagicMock(return_value=True)
        monkeypatch.setattr("sys.stdin.isatty", mock_isatty)

        # Mock input to return empty string
        mock_input = MagicMock(return_value="")
        monkeypatch.setattr("builtins.input", mock_input)

        # Mock print
        mock_print = MagicMock()
        monkeypatch.setattr("builtins.print", mock_print)

        # Mock sys.exit
        mock_exit = MagicMock()
        monkeypatch.setattr("sys.exit", mock_exit)

        # Should call sys.exit(1) after prompt returns None
        BoltzLabClient(base_url="https://lab.boltz.bio")

        mock_exit.assert_called_once_with(1)

    def test_client_initialization_non_interactive_no_prompt(self, monkeypatch):
        """Test client initialization in non-interactive environment skips prompt."""
        from unittest.mock import MagicMock

        # Mock TTY check to return False (non-interactive/CI)
        mock_isatty = MagicMock(return_value=False)
        monkeypatch.setattr("sys.stdin.isatty", mock_isatty)

        # Mock input - should NOT be called
        mock_input = MagicMock()
        monkeypatch.setattr("builtins.input", mock_input)

        # Mock print
        mock_print = MagicMock()
        monkeypatch.setattr("builtins.print", mock_print)

        # Mock sys.exit
        mock_exit = MagicMock()
        monkeypatch.setattr("sys.exit", mock_exit)

        # Should call sys.exit(1) without prompting
        BoltzLabClient(base_url="https://lab.boltz.bio")

        # Verify input was never called
        assert not mock_input.called
        mock_exit.assert_called_once_with(1)

    def test_client_initialization_keyboard_interrupt(self, monkeypatch):
        """Test client initialization handles KeyboardInterrupt gracefully."""
        from unittest.mock import MagicMock

        # Mock TTY check
        mock_isatty = MagicMock(return_value=True)
        monkeypatch.setattr("sys.stdin.isatty", mock_isatty)

        # Mock input to raise KeyboardInterrupt
        mock_input = MagicMock(side_effect=KeyboardInterrupt)
        monkeypatch.setattr("builtins.input", mock_input)

        # Mock print
        mock_print = MagicMock()
        monkeypatch.setattr("builtins.print", mock_print)

        # Mock sys.exit
        mock_exit = MagicMock()
        monkeypatch.setattr("sys.exit", mock_exit)

        # Should call sys.exit(1) after handling interrupt
        BoltzLabClient(base_url="https://lab.boltz.bio")

        mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_submit_prediction(self, client, httpx_mock, mock_factory):
        """Test submitting a prediction."""
        mock_factory.add_submission(httpx_mock)

        job = await client.submit_prediction(
            complex_data={"sequences": []},
            prediction_name="test",
        )

        assert isinstance(job, PredictionJob)
        assert job.prediction_id == mock_factory.default_id

    @pytest.mark.asyncio
    async def test_submit_job_from_yaml(self, client, httpx_mock, sample_yaml_file, mock_factory):
        """Test submitting a job from YAML file."""
        mock_factory.add_submission(httpx_mock)
        job = await client.submit_job_from_yaml(sample_yaml_file)

        assert isinstance(job, PredictionJob)
        assert job.prediction_id == mock_factory.default_id

    @pytest.mark.asyncio
    async def test_submit_job_from_yaml_url(self, client, httpx_mock, yaml_content, mock_factory):
        """Test submitting a job from YAML URL."""
        # Mock the YAML URL request
        httpx_mock.add_response(
            method="GET",
            url="https://example.com/test.yaml",
            text=yaml_content,
        )

        # Mock the submission
        mock_factory.add_submission(httpx_mock)
        job = await client.submit_job_from_yaml("https://example.com/test.yaml")

        assert isinstance(job, PredictionJob)
        assert job.prediction_id == mock_factory.default_id

    @pytest.mark.asyncio
    async def test_get_prediction_status(self, client, httpx_mock, mock_factory):
        """Test getting prediction status."""
        mock_factory.add_status(httpx_mock)
        status = await client.get_prediction_status(mock_factory.default_id)

        assert isinstance(status, PredictionStatus)
        assert status.prediction_id == mock_factory.default_id
        assert status.prediction_status == "RUNNING"

    @pytest.mark.asyncio
    async def test_authentication_error(self, httpx_mock, mock_factory):
        """Test authentication error handling."""
        mock_factory.add_error(httpx_mock, "123")

        client = BoltzLabClient(api_key="invalid-key", base_url="https://lab.boltz.bio")
        with pytest.raises(BoltzAuthenticationError):
            await client.get_prediction_status("123")
        await client.close()

    @pytest.mark.asyncio
    async def test_wait_for_prediction_completion(self, client, httpx_mock, mock_factory):
        """Test waiting for prediction completion."""
        # Add both RUNNING and COMPLETED responses
        mock_factory.add_status(httpx_mock, "123", status="RUNNING")
        mock_factory.add_status(httpx_mock, "123", status="COMPLETED")

        progress_updates = []

        def track_progress(status):
            progress_updates.append(status.prediction_status)

        result = await client.wait_for_prediction(
            "123",
            polling_interval=0.1,
            progress_callback=track_progress,
        )

        assert result.prediction_status == "COMPLETED"
        assert progress_updates == ["RUNNING", "COMPLETED"]

    @pytest.mark.asyncio
    async def test_download_results(self, client, httpx_mock, tmp_path, mock_factory):
        """Test downloading prediction results in archive format (default)."""
        mock_factory.add_download(httpx_mock, "123")

        # Mock downloading tar.gz file
        tar_data = b"test tar data"
        httpx_mock.add_response(
            method="GET",
            url="https://s3.example.com/results.tar.gz",
            content=tar_data,
        )

        output_path = await client.download_results("123", str(tmp_path))

        assert Path(output_path).exists()
        assert output_path.endswith(".tar.gz")
        assert Path(output_path).read_bytes() == tar_data

    @pytest.mark.asyncio
    async def test_download_results_json(self, client, httpx_mock, tmp_path, mock_factory):
        """Test downloading results in JSON format."""
        result_data = {"status": "completed", "output": {"processedResults": {"sample1": {"fileUrls": {}}}}}

        # Use mock_factory but override with JSON results
        response = mock_factory.prediction_response("123", status="COMPLETED")
        response["predictionResults"] = result_data
        httpx_mock.add_response(
            method="GET",
            url=f"{mock_factory.base_url}/api/v1/connect/predictions/123",
            json=response,
        )

        output_path = await client.download_results("123", str(tmp_path), output_format="json")

        assert Path(output_path).exists()
        assert output_path.endswith(".json")
        with Path(output_path).open() as f:
            downloaded = json.load(f)
        assert downloaded == result_data

    @pytest.mark.asyncio
    async def test_async_check(self, client):
        """Test that all public methods are async."""
        async_methods = [
            "submit_prediction",
            "submit_job_from_yaml",
            "submit_job_from_dict",
            "get_prediction_status",
            "list_predictions",
            "get_prediction_output_url",
            "download_results",
            "wait_for_prediction",
        ]

        for method_name in async_methods:
            method = getattr(client, method_name)
            assert asyncio.iscoroutinefunction(method), f"{method_name} should be async"

    @pytest.mark.asyncio
    async def test_multiple_status_transitions(self, client, httpx_mock, mock_factory):
        """Test prediction status transitions through multiple states."""
        states = ["QUEUED", "RUNNING", "PROCESSING", "COMPLETED"]
        for state in states:
            mock_factory.add_status(httpx_mock, "456", status=state, name=f"test-{state}")

        collected_states = []
        for _ in states:
            status = await client.get_prediction_status("456")
            collected_states.append(status.prediction_status)

        assert collected_states == states

    @pytest.mark.asyncio
    async def test_failed_prediction(self, client, httpx_mock, mock_factory):
        """Test handling of failed predictions."""
        mock_factory.add_status(httpx_mock, "789", status="FAILED", predictionStageDescription="Error occurred", error="Invalid input data")

        status = await client.get_prediction_status("789")
        assert status.prediction_status == "FAILED"
        assert "Error occurred" in status.prediction_stage_description
