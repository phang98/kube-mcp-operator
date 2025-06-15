import sys
import types
import importlib
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import kopf
except ImportError:  # pragma: no cover - offline fallback
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
except ImportError:  # pragma: no cover - offline fallback
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
        if name == "exist-mcp":
            return True
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

op = importlib.reload(importlib.import_module('mcp_operator.mcp_operator'))


def test_service_already_exists():
    meta = types.SimpleNamespace(
        annotations={'mcp-server': 'true'},
        name='exist',
        namespace='default',
        labels={'app': 'demo'}
    )
    op.api.created = None
    spec = {'template': {'spec': {'containers': [{'name': 'main'}]}}}
    op.apps.patched = None
    op.deployment_created(body={}, spec=spec, meta=meta)
    # Since the service exists, no new service should be created
    assert op.api.created is None
    assert op.apps.patched is None


def test_error_propagates():
    def bad_read(name, namespace):
        raise kubernetes.client.exceptions.ApiException(status=500)
    op.api.read_namespaced_service = bad_read
    meta = types.SimpleNamespace(
        annotations={'mcp-server': 'true'},
        name='broken',
        namespace='default',
        labels={}
    )
    with pytest.raises(kubernetes.client.exceptions.ApiException):
        op.deployment_created(body={}, spec={'template': {'spec': {'containers': [{'name': 'main'}]}}}, meta=meta)
