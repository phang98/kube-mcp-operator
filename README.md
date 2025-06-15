# Kube MCP Operator

This repository provides a minimal implementation of a Kubernetes operator and sidecar that expose microservice APIs as MCP services.

## Components

- **Sidecar** - Lightweight FastAPI application that proxies requests to the main container and exposes its OpenAPI specification from a configurable path.
- **Operator** - A Kopf based operator watching for deployments annotated with `mcp-server: "true"` and creating a service for the sidecar.
- **CRD** - `MCPConfig` allows selecting deployments by label and exposing only those annotated.
- **Helm chart** - Installs the operator and CRD.

## Architecture

```mermaid
graph TD
    subgraph Pod
        App[Microservice]
        Sidecar[MCP Sidecar]
        App <--> Sidecar
    end
    Client --> Sidecar
    Operator[MCP Operator] -- watches --> Deployment["Deployment with mcp-server=true"]
    Operator -- creates --> Service
    Service --> Sidecar
```

## Building

Sidecar image:
```bash
docker build -t mcp-sidecar ./sidecar
```

Operator image:
```bash
docker build -t mcp-operator ./mcp_operator
```

## Installing with Helm

```bash
helm install mcp-operator charts/mcp-operator
```

## Usage

Add the sidecar container to a deployment and annotate the deployment:

```yaml
metadata:
  annotations:
    mcp-server: "true"
```

The operator will create a service `<deployment>-mcp` exposing port `8000`.

### Configuration

The sidecar locates the upstream service using environment variables:

- `SERVICE_HOST` – hostname of the microservice (default `localhost`)
- `SERVICE_PORT` – port of the microservice (default `80`)
- `OPENAPI_PATH` – path to the OpenAPI or Swagger file including the file name
  (default `openapi.json`)

Requests to `/openapi.json` on the sidecar return the file from
`http://$SERVICE_HOST:$SERVICE_PORT/$OPENAPI_PATH`.

## Testing

Run the unit tests with coverage:

```bash
pip install -e .[dev]
pytest --cov=sidecar --cov=mcp_operator --cov-report=term --cov-fail-under=80
```

## CI Artifacts

The GitHub Actions workflow builds the sidecar Docker image and packages the
Helm chart on each push. When changes land on `main`, a release is created that
attaches:

- `mcp-sidecar.tar` – the Docker image saved as a tarball
- `mcp-operator-<version>.tgz` – the packaged Helm chart

Version changes are tracked in [CHANGELOG.md](CHANGELOG.md). New releases are
automatically tagged using semantic versioning when changes merge to `main`.
