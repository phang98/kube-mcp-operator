import sys
import types
import importlib
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import kopf
except ImportError:  # pragma: no cover - fallback for offline testing
    kopf = types.SimpleNamespace(
        on=types.SimpleNamespace(
            startup=lambda *a, **k: (lambda f: f),
            create=lambda *a, **k: (lambda f: f),
        ),
        OperatorSettings=object,
    )
    sys.modules['kopf'] = kopf

try:
    import kubernetes
except ImportError:  # pragma: no cover - fallback for offline testing
    class _DummyExc(Exception):
        def __init__(self, status=0):
            self.status = status

    class _V1ObjectMeta:
        def __init__(self, name=None, labels=None):
            self.name = name
            self.labels = labels

    class _V1ServiceSpec:
        def __init__(self, selector=None, ports=None):
            self.selector = selector
            self.ports = ports

    class _V1ServicePort:
        def __init__(self, port=None, target_port=None):
            self.port = port
            self.target_port = target_port

    class _V1Service:
        def __init__(self, metadata=None, spec=None):
            self.metadata = metadata
            self.spec = spec

    kubernetes = types.SimpleNamespace(
        config=types.SimpleNamespace(load_incluster_config=lambda: None),
        client=types.SimpleNamespace(
            CoreV1Api=lambda: None,
            AppsV1Api=lambda: None,
            exceptions=types.SimpleNamespace(ApiException=_DummyExc),
            V1Service=_V1Service,
            V1ObjectMeta=_V1ObjectMeta,
            V1ServiceSpec=_V1ServiceSpec,
            V1ServicePort=_V1ServicePort,
        ),
    )
    sys.modules['kubernetes'] = kubernetes
else:
    kubernetes.config.load_incluster_config = lambda: None

class DummyCoreV1Api:
    def __init__(self):
        self.created = None
    def read_namespaced_service(self, name, namespace):
        raise kubernetes.client.exceptions.ApiException(status=404)
    def create_namespaced_service(self, namespace, svc):
        self.created = svc.metadata.name

class DummyAppsV1Api:
    def __init__(self):
        self.patched = None

    def list_namespaced_deployment(self, namespace, label_selector=None):
        return types.SimpleNamespace(items=[])

    def list_deployment_for_all_namespaces(self):
        return types.SimpleNamespace(items=[])

    def patch_namespaced_deployment(self, name, namespace, body):
        self.patched = (name, namespace, body)

kubernetes.client.CoreV1Api = DummyCoreV1Api
kubernetes.client.AppsV1Api = DummyAppsV1Api

op = importlib.import_module('mcp_operator.mcp_operator')

def test_deployment_created():
    meta = types.SimpleNamespace(
        annotations={'mcp-server': 'true'},
        name='demo',
        namespace='default',
        labels={'app': 'demo'}
    )
    spec = {
        'template': {
            'spec': {
                'containers': [{'name': 'main'}]
            }
        }
    }
    op.deployment_created(body={}, spec=spec, meta=meta)
    assert op.api.created == 'demo-mcp'
    assert op.apps.patched[0] == 'demo'
    patched_containers = op.apps.patched[2]['spec']['template']['spec']['containers']
    assert any(c.get('name') == 'mcp-sidecar' for c in patched_containers)

def test_deployment_created_skip():
    meta = types.SimpleNamespace(annotations={'mcp-server': 'false'}, name='demo', namespace='default', labels={'app': 'demo'})
    op.api.created = None
    spec = {'template': {'spec': {'containers': [{'name': 'main'}]}}}
    op.apps.patched = None
    op.deployment_created(body={}, spec=spec, meta=meta)
    assert op.api.created is None
    assert op.apps.patched is None

def test_mcpconfig_created():
    deploy_meta = types.SimpleNamespace(annotations={'mcp-server': 'true'}, name='demo', namespace='default', labels={'app': 'demo'})
    deployment = types.SimpleNamespace(
        metadata=deploy_meta,
        spec=types.SimpleNamespace(to_dict=lambda: {
            'template': {'spec': {'containers': [{'name': 'main'}]}}
        }),
        to_dict=lambda: {}
    )
    op.apps.list_namespaced_deployment = lambda namespace, label_selector=None: types.SimpleNamespace(items=[deployment])
    op.api.created = None
    op.apps.patched = None
    op.mcpconfig_created(body={}, spec={'selector': {'app': 'demo'}}, meta={'namespace': 'default'})
    assert op.api.created == 'demo-mcp'
    assert op.apps.patched[0] == 'demo'


def test_startup_injects_existing():
    meta = types.SimpleNamespace(
        annotations={'mcp-server': 'true'},
        name='old',
        namespace='default',
        labels={'app': 'demo'}
    )
    deployment = types.SimpleNamespace(
        metadata=meta,
        spec=types.SimpleNamespace(to_dict=lambda: {
            'template': {'spec': {'containers': [{'name': 'main'}]}}
        }),
        to_dict=lambda: {}
    )
    op.apps.list_deployment_for_all_namespaces = lambda: types.SimpleNamespace(items=[deployment])
    op.api.created = None
    op.apps.patched = None
    op.inject_existing_deployments()
    assert op.api.created == 'old-mcp'
    assert op.apps.patched[0] == 'old'
