# Contributing

Thank you for your interest in contributing to Kube MCP Operator!

## Development setup

- Install the project with development dependencies:
  ```bash
  pip install -e .[dev]
  ```
- Run the tests with coverage (requires internet access to install optional dependencies):
  ```bash
  pytest --cov=sidecar --cov=mcp_operator --cov-report=term --cov-fail-under=80
  ```

## Submitting changes

1. Fork the repository and create your branch from `main`.
2. Make your changes and ensure the tests pass.
3. Open a pull request describing your changes.

Please see [README.md](README.md) for more details about the project.
