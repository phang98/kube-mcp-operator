import pytest
kopf = pytest.importorskip('kopf')
kubernetes = pytest.importorskip('kubernetes')
import types
import importlib

kubernetes.config.load_incluster_config = lambda: None

class DummyCoreV1Api:
    def __init__(self):
        self.created = None
    def read_namespaced_service(self, name, namespace):
        raise kubernetes.client.exceptions.ApiException(status=404)
    def create_namespaced_service(self, namespace, svc):
        self.created = svc.metadata.name

class DummyAppsV1Api:
    def list_namespaced_deployment(self, namespace, label_selector=None):
        return types.SimpleNamespace(items=[])

kubernetes.client.CoreV1Api = DummyCoreV1Api
kubernetes.client.AppsV1Api = DummyAppsV1Api

op = importlib.import_module('operator.mcp_operator')

def test_deployment_created():
    meta = types.SimpleNamespace(annotations={'mcp-server': 'true'}, name='demo', namespace='default', labels={'app': 'demo'})
    op.deployment_created(body={}, spec={}, meta=meta)
    assert op.api.created == 'demo-mcp'

def test_deployment_created_skip():
    meta = types.SimpleNamespace(annotations={'mcp-server': 'false'}, name='demo', namespace='default', labels={'app': 'demo'})
    op.api.created = None
    op.deployment_created(body={}, spec={}, meta=meta)
    assert op.api.created is None

def test_mcpconfig_created():
    deploy_meta = types.SimpleNamespace(annotations={'mcp-server': 'true'}, name='demo', namespace='default', labels={'app': 'demo'})
    deployment = types.SimpleNamespace(
        metadata=deploy_meta,
        spec=types.SimpleNamespace(to_dict=lambda: {}),
        to_dict=lambda: {}
    )
    op.apps.list_namespaced_deployment = lambda namespace, label_selector=None: types.SimpleNamespace(items=[deployment])
    op.api.created = None
    op.mcpconfig_created(body={}, spec={'selector': {'app': 'demo'}}, meta={'namespace': 'default'})
    assert op.api.created == 'demo-mcp'
