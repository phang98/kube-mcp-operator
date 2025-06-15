# Kube MCP Operator

This repository provides a minimal implementation of a Kubernetes operator and sidecar that expose microservice APIs as MCP services.

## Components

- **Sidecar** - Lightweight FastAPI application that proxies requests to the main container and exposes its OpenAPI specification.
- **Operator** - A Kopf based operator watching for deployments annotated with `mcp-server: "true"` and creating a service for the sidecar.
- **CRD** - `MCPConfig` allows selecting deployments by label and exposing only those annotated.
- **Helm chart** - Installs the operator and CRD.

## Building

Sidecar image:
```bash
docker build -t mcp-sidecar ./sidecar
```

Operator image:
```bash
docker build -t mcp-operator ./operator
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
