"""Command-line interface for Boltz Lab API."""

import asyncio
import json
import logging
import os
import sys

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .client import BoltzLabClient
from .config import get_config
from .exceptions import BoltzAPIError, BoltzConnectionError
from .models import JobStatus, PredictionStatus
from .prediction_flags import Flags
from .prediction_flags import add_click_options as add_prediction_flags_click_options

console = Console()
logger = logging.getLogger(__name__)

# Set up logging to show retry attempts
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()])

# Suppress httpx HTTP request logs for CLI usage by default
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def run_async(coro):
    """Helper to run async functions in Click commands."""
    return asyncio.run(coro)


def check_api_key(api_key: str | None) -> None:
    """Check if API key is provided and show helpful error if not."""
    if not api_key:
        config = get_config()
        signup_url = os.getenv("BOLTZ_SIGNUP_URL") or config.get_signup_url() or "https://lab.boltz.bio"
        config_path = config.config_path

        console.print("[red]Error: API key must be provided via --api-key or BOLTZ_API_KEY environment variable[/red]")
        console.print("\n[yellow]To get an API key:[/yellow]")
        console.print(f"1. Visit {signup_url}")
        console.print("2. Sign up for an account")
        console.print("3. Find your API key in the settings")
        console.print("\n[dim]Then you can either:[/dim]")
        console.print("  • Set it as an environment variable:")
        console.print("    export BOLTZ_API_KEY=your-api-key-here")
        console.print("  • Save it in the config file:")
        console.print("    boltz-lab config --api-key your-api-key-here")
        console.print(f"  • Or manually create {config_path}")
        sys.exit(1)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging including HTTP requests")
@click.pass_context
def cli(ctx, debug):
    """Boltz Lab API CLI."""
    # Store debug flag in context for use by subcommands
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug

    # If debug mode is enabled, set httpx loggers to DEBUG level
    if debug:
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logging.getLogger("httpcore").setLevel(logging.DEBUG)
        logger.info("Debug mode enabled - HTTP requests will be logged")


@cli.command()
@click.argument("yaml_file")
@click.option("--name", help="Name for the prediction")
@click.option("--no-wait", is_flag=True, help="Wait for job completion (implies --no-download)")
@click.option("--no-download", is_flag=True, help="Download results after completion")
@click.option("--output", "-o", "output_dir", default=".", help="Output directory for downloaded results")
@click.option("--format", "-f", "output_format", type=click.Choice(["archive", "json"]), default="archive", help="Download format (default: archive)")
@click.option("--polling-interval", default=5, help="Polling interval in seconds when waiting")
@click.option("--timeout", type=int, help="Timeout in seconds when waiting")
@click.option("--api-key", envvar="BOLTZ_API_KEY", help="API key (or use BOLTZ_API_KEY env var)")
@click.option("--api-url", envvar="BOLTZ_API_ENDPOINT", help="API URL (or use BOLTZ_API_ENDPOINT env var)")
@add_prediction_flags_click_options
def predict(
    yaml_file: str,
    name: str | None,
    no_wait: bool,
    no_download: bool,
    output_dir: str,
    output_format: str,
    polling_interval: int,
    timeout: int | None,
    api_key: str | None,
    api_url: str | None,
    **flags: Flags,  # Capture all flag arguments
):
    """Submit a prediction job from a YAML file or URL.

    YAML_FILE can be a local file path or an HTTP/HTTPS URL.

    Examples:
        # Submit and download results when ready
        boltz-lab predict job.yaml

        # Submit, wait, and download to specific directory
        boltz-lab predict job.yaml --output ./results

        # Submit and download as JSON format
        boltz-lab predict job.yaml --format json
    """

    # If download is requested, we need to wait
    if no_wait:
        no_download = True

    async def submit_and_wait():
        async with BoltzLabClient(api_key=api_key, base_url=api_url) as client:
            try:
                # Submit the job
                with console.status(f"Submitting prediction from {yaml_file}..."):
                    job = await client.submit_job_from_yaml(
                        yaml_file,
                        prediction_name=name,
                        flags=flags,
                    )

                console.print("[green]✓[/green] Prediction submitted successfully!")
                console.print(f"Prediction ID: [bold]{job.prediction_id}[/bold]")

                if no_wait:
                    # Just show the submission info and terminate
                    submission_info = {
                        "prediction_id": job.prediction_id,
                        "status": "submitted",
                    }
                    console.print_json(json.dumps(submission_info))
                    return

                # Wait for completion
                console.print("\nWaiting for completion...")

                # Progress tracking
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task("Processing...", total=None)

                    def update_progress(status: PredictionStatus):
                        progress.update(
                            task,
                            description=f"Status: {status.prediction_status}",
                        )

                    result = await job.wait_for_completion(
                        polling_interval=polling_interval,
                        timeout=timeout,
                        progress_callback=update_progress,
                    )

                console.print("\n[green]✓[/green] Prediction completed!")

                if no_download:
                    # Display results in JSON format without download
                    output_data = {
                        "prediction_id": result.prediction_id,
                        "status": result.prediction_status,
                        "created_at": result.created_at.isoformat(),
                        "completed_at": (result.completed_at.isoformat() if result.completed_at else None),
                    }
                else:
                    # Download results
                    console.print(f"\nDownloading {output_format} results...")
                    try:
                        output_path = await job.download_results(output_dir=output_dir, output_format=output_format)
                        console.print(f"[green]✓[/green] Results downloaded to: {output_path}")

                        # Display results in JSON format including download path
                        output_data = {
                            "prediction_id": result.prediction_id,
                            "status": result.prediction_status,
                            "created_at": result.created_at.isoformat(),
                            "completed_at": (result.completed_at.isoformat() if result.completed_at else None),
                            "download_path": output_path,
                            "format": output_format,
                        }
                    except Exception as e:
                        console.print(f"[red]Error downloading results: {e}[/red]")
                        # Still show completion info even if download fails
                        output_data = {
                            "prediction_id": result.prediction_id,
                            "status": result.prediction_status,
                            "created_at": result.created_at.isoformat(),
                            "completed_at": (result.completed_at.isoformat() if result.completed_at else None),
                            "download_error": str(e),
                        }

                console.print_json(json.dumps(output_data))

            except BoltzConnectionError as e:
                console.print("\n[red]Connection failed after 3 retry attempts[/red]")
                console.print(f"[dim]{e}[/dim]")
                console.print("\n[yellow]Troubleshooting tips:[/yellow]")
                console.print("  • Check if the API server is running")
                console.print("  • Verify the API endpoint is correct")
                console.print("  • Check your internet connection")
                console.print("  • If using localhost, ensure the server is started")
                console.print("  • Check if you're behind a firewall or proxy")
                sys.exit(1)
            except BoltzAPIError as e:
                console.print(f"[red]Error: {e}[/red]")
                if e.response_data:
                    console.print(f"Response: {json.dumps(e.response_data, indent=2)}")
                sys.exit(1)
            except Exception as e:
                console.print(f"[red]Unexpected error: {e}[/red]")
                import traceback

                console.print(traceback.format_exc())
                sys.exit(1)

    run_async(submit_and_wait())


@cli.command()
@click.argument("prediction_id")
@click.option("--api-key", envvar="BOLTZ_API_KEY", help="API key (or use BOLTZ_API_KEY env var)")
@click.option("--api-url", envvar="BOLTZ_API_ENDPOINT", help="API URL (or use BOLTZ_API_ENDPOINT env var)")
def status(prediction_id: str, api_key: str | None, api_url: str | None):
    """Check the status of a prediction job."""

    async def get_status():
        async with BoltzLabClient(api_key=api_key, base_url=api_url) as client:
            try:
                status = await client.get_prediction_status(prediction_id)

                # Output as JSON
                output = {
                    "prediction_id": status.prediction_id,
                    "name": status.prediction_name,
                    "status": status.prediction_status,
                    "created_at": status.created_at.isoformat(),
                    "started_at": status.started_at.isoformat() if status.started_at else None,
                    "completed_at": status.completed_at.isoformat() if status.completed_at else None,
                }
                console.print_json(json.dumps(output))

            except BoltzConnectionError as e:
                console.print(f"[red]Connection Error: {e}[/red]")
                sys.exit(1)
            except BoltzAPIError as e:
                console.print(f"[red]Error: {e}[/red]")
                sys.exit(1)

    run_async(get_status())


@cli.command()
@click.option("--status", type=click.Choice([s.value for s in JobStatus]), help="Filter by status")
@click.option("--limit", default=20, help="Maximum number of results")
@click.option("--offset", default=0, help="Offset for pagination")
@click.option("--api-key", envvar="BOLTZ_API_KEY", help="API key (or use BOLTZ_API_KEY env var)")
@click.option("--api-url", envvar="BOLTZ_API_ENDPOINT", help="API URL (or use BOLTZ_API_ENDPOINT env var)")
def list(
    status: str | None,
    limit: int,
    offset: int,
    api_key: str | None,
    api_url: str | None,
):
    """List prediction jobs."""

    async def list_predictions():
        async with BoltzLabClient(api_key=api_key, base_url=api_url) as client:
            try:
                status_filter = JobStatus(status) if status else None
                result = await client.list_predictions(
                    status=status_filter,
                    limit=limit,
                    offset=offset,
                )

                # Output as JSON
                output = {
                    "total": result.total,
                    "predictions": [
                        {
                            "prediction_id": p.prediction_id,
                            "name": p.prediction_name,
                            "status": p.prediction_status,
                            "created_at": p.created_at.isoformat(),
                        }
                        for p in result.predictions
                    ],
                }
                console.print_json(json.dumps(output))

            except BoltzConnectionError as e:
                console.print(f"[red]Connection Error: {e}[/red]")
                sys.exit(1)
            except BoltzAPIError as e:
                console.print(f"[red]Error: {e}[/red]")
                sys.exit(1)

    run_async(list_predictions())


@cli.command()
@click.argument("prediction_id")
@click.option("--output", "-o", default=".", help="Output directory for results")
@click.option("--format", "-f", type=click.Choice(["archive", "json"]), default="archive", help="Output format (default: archive)")
@click.option("--filename", help="Custom filename (without extension)")
@click.option("--no-wait", is_flag=True, help="Skip waiting for prediction to complete (fail if not ready)")
@click.option("--polling-interval", default=5, help="Seconds between status checks when waiting (default: 5)")
@click.option("--timeout", default=None, type=int, help="Maximum seconds to wait (default: no timeout)")
@click.option("--api-key", envvar="BOLTZ_API_KEY", help="API key (or use BOLTZ_API_KEY env var)")
@click.option("--api-url", envvar="BOLTZ_API_ENDPOINT", help="API URL (or use BOLTZ_API_ENDPOINT env var)")
def download(
    prediction_id: str,
    output: str,
    format: str,
    filename: str | None,
    no_wait: bool,
    polling_interval: int,
    timeout: int | None,
    api_key: str | None,
    api_url: str | None,
):
    """Download prediction results.

    By default, waits for the prediction to complete then downloads.
    Use --no-wait to skip waiting (will fail if prediction is not complete).

    Examples:
        # Wait for completion and download (default)
        boltz-lab download PREDICTION_ID

        # Download immediately (fails if not complete)
        boltz-lab download PREDICTION_ID --no-wait

        # Download to specific directory
        boltz-lab download PREDICTION_ID --output ./results

        # Download as JSON format
        boltz-lab download PREDICTION_ID --format json

        # Custom filename
        boltz-lab download PREDICTION_ID --filename my_results
    """

    async def download_results():
        async with BoltzLabClient(api_key=api_key, base_url=api_url) as client:
            try:
                if not no_wait:
                    # Wait for completion first
                    console.print("Waiting for completion...")

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        TimeElapsedColumn(),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Processing...", total=None)

                        def update_progress(status: PredictionStatus):
                            progress.update(
                                task,
                                description=f"Status: {status.prediction_status}",
                            )

                        await client.wait_for_prediction(
                            prediction_id,
                            polling_interval=polling_interval,
                            timeout=timeout,
                            progress_callback=update_progress,
                        )

                    console.print("\n[green]✓[/green] Prediction completed!")

                status_msg = f"Downloading {format} results..."
                with console.status(status_msg):
                    output_path = await client.download_results(prediction_id, output, output_format=format, output_filename=filename)

                console.print(f"[green]✓[/green] Results downloaded to: {output_path}")

                # Output as JSON
                output_json = {
                    "prediction_id": prediction_id,
                    "output_path": output_path,
                    "format": format,
                }
                console.print_json(json.dumps(output_json))

            except BoltzConnectionError as e:
                console.print(f"\n[red]Connection Error: {e}[/red]")
                sys.exit(1)
            except BoltzAPIError as e:
                console.print(f"\n[red]Error: {e}[/red]")
                sys.exit(1)

    run_async(download_results())


@cli.command()
@click.option("--api-key", help="Set the API key")
@click.option("--endpoint", help="Set the API endpoint URL")
@click.option("--signup-url", help="Set the signup URL")
@click.option("--show", is_flag=True, help="Show current configuration")
def config(api_key: str | None, endpoint: str | None, signup_url: str | None, show: bool):
    """Manage Boltz Lab configuration.

    Examples:
        # Set API key
        boltz-lab config --api-key YOUR_API_KEY

        # Set custom endpoint
        boltz-lab config --endpoint https://custom.boltz.bio

        # Set signup URL
        boltz-lab config --signup-url https://lab.boltz.bio

        # Show current configuration
        boltz-lab config --show
    """
    config_obj = get_config()

    if show:
        # Show current configuration
        console.print(f"[bold]Configuration file:[/bold] {config_obj.config_path}")
        console.print()

        # Check all sources
        sources = [
            ("Config file", config_obj.get_api_key(), config_obj.get_endpoint(), config_obj.get_signup_url()),
            ("Environment", os.getenv("BOLTZ_API_KEY"), os.getenv("BOLTZ_API_ENDPOINT"), os.getenv("BOLTZ_SIGNUP_URL")),
        ]

        console.print("[bold]Current settings:[/bold]")
        for source, key, url, signup in sources:
            if key or url or signup:
                console.print(f"\n[yellow]{source}:[/yellow]")
                if key:
                    masked_key = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
                    console.print(f"  API Key: {masked_key}")
                if url:
                    console.print(f"  Endpoint: {url}")
                if signup:
                    console.print(f"  Signup URL: {signup}")

        # Show effective values
        try:
            client = BoltzLabClient()
            console.print("\n[bold green]Effective values:[/bold green]")
            masked_key = client.api_key[:8] + "..." + client.api_key[-4:] if len(client.api_key) > 12 else "***"
            console.print(f"  API Key: {masked_key}")
            console.print(f"  Endpoint: {client.base_url}")
            console.print(f"  Signup URL: {client.signup_url}")
        except ValueError:
            console.print("\n[bold red]No API key configured![/bold red]")

        return

    if not api_key and not endpoint and not signup_url:
        console.print("[yellow]No changes specified. Use --help for usage information.[/yellow]")
        return

    # Save configuration
    config_obj.save_config(api_key=api_key, endpoint=endpoint, signup_url=signup_url)

    console.print("[green]✓[/green] Configuration saved successfully!")
    console.print(f"Location: {config_obj.config_path}")

    if api_key:
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        console.print(f"  API Key: {masked_key}")
    if endpoint:
        console.print(f"  Endpoint: {endpoint}")
    if signup_url:
        console.print(f"  Signup URL: {signup_url}")


if __name__ == "__main__":
    cli()
