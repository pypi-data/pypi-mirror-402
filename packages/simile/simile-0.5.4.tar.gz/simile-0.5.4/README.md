# Simile API Python Client

A Python client for interacting with the Simile API server.

## Installation

```bash
pip install simile
```

## Dependencies

- `httpx>=0.20.0`
- `pydantic>=2.0.0`

## Usage

```python
from simile import Simile

client = Simile(api_key="your_api_key")
```

## Publishing

1. Bump the version in `pyproject.toml`
2. Commit and push your changes
3. Go to the **Actions** tab in GitHub
4. Select **Build and Publish to PyPI** workflow
5. Click **Run workflow** and select the branch to run from
6. The workflow will automatically build and publish to PyPI

The workflow uses the `PYPI_API_TOKEN` secret configured in the repository settings.