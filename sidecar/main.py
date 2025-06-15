import os
from fastapi import FastAPI, Request, Response
import httpx

# Disable the default OpenAPI route so we can proxy the underlying
# service's specification instead of the sidecar's.
app = FastAPI(title="MCP Sidecar", docs_url="/docs", openapi_url=None)

SERVICE_HOST = os.environ.get("SERVICE_HOST", "localhost")
SERVICE_PORT = os.environ.get("SERVICE_PORT", "80")
OPENAPI_PATH = os.environ.get("OPENAPI_PATH", "openapi.json")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    method = request.method
    url = f"http://{SERVICE_HOST}:{SERVICE_PORT}/{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.request(method, url, headers=dict(request.headers), content=await request.body())
    return Response(content=resp.content, status_code=resp.status_code, headers=resp.headers)

@app.get("/openapi.json")
async def openapi_spec():
    """Fetch the upstream service's OpenAPI spec."""
    path = OPENAPI_PATH.lstrip("/")
    url = f"http://{SERVICE_HOST}:{SERVICE_PORT}/{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    return Response(content=resp.content, media_type="application/json")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
