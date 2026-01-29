[![codecov](https://codecov.io/gh/SoftwareVerse/userverse-python-client/branch/main/graph/badge.svg?token=YOUR_TOKEN)](https://codecov.io/gh/SoftwareVerse/userverse-python-client)


# userverse-python-client

Python client for the Userverse HTTP server.

## Installation

Create and activate a virtual environment, then install the project in editable mode:

## linux configuration
```bash
uv venv
source .venv\Scripts\activate
uv pip install -e .
```

## windows configuration
```bash
uv venv
.venv\Scripts\activate
uv pip install -e .
```
## Usage

The main package is `userverse_python_client`, which exposes `UverseUserClient`:

```python
from userverse_python_client import UverseUserClient

client = UverseUserClient(base_url="https://api.example.com")
```

## Demo

The runnable demo lives in `examples/user_demo.py`. See `examples/user_demo_README.md`
for flags and environment variables:

```bash
uv run -m examples.user_demo --help
```

## Tests

Run the unit tests with:

```bash
pytest
```

