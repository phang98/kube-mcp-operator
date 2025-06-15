import pytest
import runpy
pytest.importorskip('fastapi')
pytest.importorskip('httpx')
from fastapi.testclient import TestClient

from sidecar.main import app

class DummyResp:
    def __init__(self, content=b"{}", status_code=200, headers=None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}

async def dummy(method, url, headers=None, content=None):
    return DummyResp(b"ok")

async def dummy_get(url):
    return DummyResp(b'{"openapi": "3.0"}')

class DummyClient:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        pass
    async def request(self, method, url, headers=None, content=None):
        return await dummy(method, url, headers, content)
    async def get(self, url):
        return await dummy_get(url)

def test_openapi(monkeypatch):
    monkeypatch.setattr('sidecar.main.httpx.AsyncClient', lambda: DummyClient())
    client = TestClient(app)
    resp = client.get('/openapi.json')
    assert resp.status_code == 200
    assert resp.json() == {'openapi': '3.0'}

def test_proxy(monkeypatch):
    monkeypatch.setattr('sidecar.main.httpx.AsyncClient', lambda: DummyClient())
    client = TestClient(app)
    resp = client.get('/foo')
    assert resp.status_code == 200
    assert resp.text == 'ok'

def test_main_entry(monkeypatch):
    monkeypatch.setattr('uvicorn.run', lambda app, host, port: (app, host, port))
    result = runpy.run_module('sidecar.main', run_name='__main__')
    assert result is not None
