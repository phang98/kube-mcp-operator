import kopf
import kubernetes

MCP_LABEL = 'mcp-server'
SIDE_CAR_PORT = 8000

kubernetes.config.load_incluster_config()
api = kubernetes.client.CoreV1Api()
apps = kubernetes.client.AppsV1Api()

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = 'INFO'

@kopf.on.create('apps', 'v1', 'deployments')
def deployment_created(body, spec, meta, **kwargs):
    annotations = meta.annotations or {}
    if annotations.get(MCP_LABEL) != 'true':
        return
    name = meta.name
    namespace = meta.namespace
    labels = meta.labels
    service_name = f"{name}-mcp"
    try:
        api.read_namespaced_service(service_name, namespace)
        return
    except kubernetes.client.exceptions.ApiException as e:
        if e.status != 404:
            raise
    # Inject the sidecar container when it is not already present
    containers = (
        spec.get("template", {}).get("spec", {}).get("containers", [])
    )
    if not any(c.get("name") == "mcp-sidecar" for c in containers):
        sidecar = {
            "name": "mcp-sidecar",
            "image": "mcp-sidecar:latest",
            "ports": [{"containerPort": SIDE_CAR_PORT}],
        }
        patch = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": containers + [sidecar]
                    }
                }
            }
        }
        apps.patch_namespaced_deployment(name, namespace, patch)
    svc = kubernetes.client.V1Service(
        metadata=kubernetes.client.V1ObjectMeta(name=service_name, labels=labels),
        spec=kubernetes.client.V1ServiceSpec(
            selector=labels,
            ports=[kubernetes.client.V1ServicePort(port=SIDE_CAR_PORT, target_port=SIDE_CAR_PORT)],
        ),
    )
    api.create_namespaced_service(namespace, svc)

# CRD handler
@kopf.on.create('mcp.mycompany.com', 'v1', 'mcpconfigs')
def mcpconfig_created(body, spec, meta, **kwargs):
    selector = spec.get('selector', {})
    namespace = meta.get('namespace')
    deployments = apps.list_namespaced_deployment(namespace, label_selector=','.join(f"{k}={v}" for k, v in selector.items()))
    for deploy in deployments.items:
        annotations = deploy.metadata.annotations or {}
        if annotations.get(MCP_LABEL) == 'true':
            deployment_created(body=deploy.to_dict(), spec=deploy.spec.to_dict(), meta=deploy.metadata, **kwargs)
