# Boltz Lab API Python Client

A Python client library for interacting with the Boltz Lab API.

## Installation

### Using pip:
```bash
pip install boltz-lab
```

### Using uv (faster):
```bash
uv pip install boltz-lab
```

## Quick Start

### Using the Python API

```python
import asyncio
from boltz_lab import BoltzLabClient

async def main():
    # Initialize client (uses BOLTZ_API_KEY env var by default)
    client = BoltzLabClient()

    # Or provide API key directly
    # client = BoltzLabClient(api_key="your-api-key")

    # Submit a job from YAML file
    job = await client.submit_job_from_yaml("examples/affinity.yaml")
    print(f"Job submitted: {job.prediction_id}")

    # Or from a URL
    # job = await client.submit_job_from_yaml("https://example.com/my-job.yaml")

    # Wait for completion
    result = await job.wait_for_completion()
    print(f"Job completed: {result}")

    # Or check status manually
    status = await client.get_prediction_status(job.prediction_id)
    print(f"Status: {status.prediction_status}")

    # Download results when ready
    if status.prediction_status == "COMPLETED":
        # Download archive (tar.gz) - default
        output_path = await client.download_results(job.prediction_id, "results/")
        print(f"Results downloaded to: {output_path}")

        # Or download as JSON
        # output_path = await client.download_results(
        #     job.prediction_id,
        #     "results/",
        #     output_format="json"
        # )
        # print(f"Results JSON downloaded to: {output_path}")

asyncio.run(main())
```

### Using the CLI

```bash
# Set your API key
boltz-lab config --api-key "your-api-key"
# Optionally override the API endpoint (default: https://lab.boltz.bio)
# boltz-lab config --api-endpoint "https://lab.boltz.bio"

# Submit a prediction job, wait, and download results (default behavior)
boltz-lab predict examples/affinity.yaml

# Submit from a URL (also waits and downloads by default)
boltz-lab predict https://raw.githubusercontent.com/jwohlwend/boltz/refs/heads/main/examples/affinity.yaml

# Submit and download to specific directory
boltz-lab predict examples/affinity.yaml --output ./results

# Submit and download as JSON format
boltz-lab predict examples/affinity.yaml --format json

# Submit without waiting (fire-and-forget)
boltz-lab predict examples/affinity.yaml --no-wait

# Submit and wait but don't download
boltz-lab predict examples/affinity.yaml --no-download

# Check status of a job
boltz-lab status <prediction-id>

# List all predictions
boltz-lab list

# List predictions with specific status
boltz-lab list --status COMPLETED

# Download results (archive format by default)
boltz-lab download <prediction-id> --output results/

# Download as JSON format
boltz-lab download <prediction-id> --output results/ --format json

# Download with custom filename
boltz-lab download <prediction-id> --filename my_results
```

## Configuration

The client can be configured through environment variables:

- `BOLTZ_API_KEY`: Your API key (required)
- `BOLTZ_API_ENDPOINT`: Base URL for the API (default: https://lab.boltz.bio)

## Job Input Format

Jobs are submitted in YAML format. See `examples/affinity.yaml` for an example:

```yaml
sequences:
  - protein:
      id: ["A"]
      sequence: MVTPEGNVSLVDESLLVGVTD...
      modifications: []
  - ligand:
      id: ["B"]
      smiles: 'N[C@@H](Cc1ccc(O)cc1)C(=O)O'
constraints: []
```

or [https://github.com/jwohlwend/boltz/tree/main/examples](https://github.com/jwohlwend/boltz/tree/main/examples)

## License

MIT
