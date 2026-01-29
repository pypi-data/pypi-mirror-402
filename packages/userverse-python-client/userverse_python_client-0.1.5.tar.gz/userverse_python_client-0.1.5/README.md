



<!-- CI status for your release workflow -->

[![CI - Release Tag](https://github.com/SoftwareVerse/userverse-python-client/actions/workflows/release.yml/badge.svg)](https://github.com/SoftwareVerse/userverse-python-client/actions/workflows/release.yml)

<!-- Latest release (SemVer-aware) badge → opens the latest release page -->

[![Latest Release](https://img.shields.io/github/v/release/SoftwareVerse/userverse-python-client?display_name=tag&sort=semver)](https://github.com/SoftwareVerse/userverse-python-client/releases/latest)

<!-- Optional: latest tag badge (from tags, even if not “GitHub Release”) -->

[![Latest Tag](https://img.shields.io/github/v/tag/SoftwareVerse/userverse-python-client?label=tag&sort=semver)](https://github.com/SoftwareVerse/userverse-python-client/releases/latest)

<!-- Optional: release date & total downloads badges -->

[![Release Date](https://img.shields.io/github/release-date/SoftwareVerse/userverse-python-client)](https://github.com/SoftwareVerse/userverse-python-client/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/SoftwareVerse/userverse-python-client/total)](https://github.com/SoftwareVerse/userverse-python-client/releases)

<!-- You already have Codecov; keep it (replace token if needed) -->

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

