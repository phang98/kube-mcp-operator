import pytest
import runpy
import json
pytest.importorskip('fastapi')
pytest.importorskip('httpx')
from fastapi.testclient import TestClient

import sidecar.main as sidecar_main
from sidecar.main import app

class DummyResp:
    def __init__(self, content=b"{}", status_code=200, headers=None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {"content-type": "application/json"}

    def json(self):
        return json.loads(self.content.decode())

    @property
    def text(self):
        return self.content.decode()

async def dummy(method, url, headers=None, content=None):
    if url.endswith('/' + sidecar_main.OPENAPI_PATH.lstrip('/')):
        return DummyResp(b'{"openapi": "3.0"}')
    return DummyResp(b'"ok"')  # valid JSON string

class DummyClient:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    async def request(self, method, url, headers=None, content=None):
        return await dummy(method, url, headers, content)
    async def get(self, url):
        return await dummy("GET", url)

def test_openapi(monkeypatch):
    monkeypatch.setattr('sidecar.main.httpx.AsyncClient', lambda: DummyClient())
    client = TestClient(app)
    resp = client.get('/openapi.json')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('openapi', '').startswith('3.')

def test_custom_openapi_path(monkeypatch):
    monkeypatch.setattr('sidecar.main.httpx.AsyncClient', lambda: DummyClient())
    monkeypatch.setattr(sidecar_main, 'OPENAPI_PATH', 'spec/swagger.json')
    client = TestClient(app)
    resp = client.get('/spec/swagger.json')  # match the new OPENAPI_PATH
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('openapi', '').startswith('3.')

def test_proxy(monkeypatch):
    monkeypatch.setattr('sidecar.main.httpx.AsyncClient', lambda: DummyClient())
    client = TestClient(app)
    resp = client.get('/foo')
    assert resp.status_code == 200
    assert resp.json() == 'ok'

def test_main_entry(monkeypatch):
    monkeypatch.setattr('uvicorn.run', lambda app, host, port: (app, host, port))
    result = runpy.run_module('sidecar.main', run_name='__main__')
    assert result is not None
