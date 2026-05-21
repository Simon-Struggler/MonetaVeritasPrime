import httpx
from config import settings
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_MAP = {
    "auth": settings.AUTH_SERVICE_URL,
    "catalog": settings.CATALOG_SERVICE_URL,
    "collections": settings.COLLECTIONS_SERVICE_URL,
    "auction": settings.AUCTION_SERVICE_URL,
}

# === Эндпоинт health должен быть ПЕРВЫМ ===
@app.get("/health")
def health():
    return {"status": "ok"}

# === Общий прокси для всех остальных путей ===
@app.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def gateway(request: Request, path: str):
    for prefix, url in SERVICE_MAP.items():
        if path.startswith(prefix):
            target_url = f"{url}/{path}"
            break
    else:
        raise HTTPException(404, "Not found")

    headers = {}
    for key, value in request.headers.items():
        if key.lower() == "host":
            continue
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="ignore")
        headers[key] = value

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=await request.body(),
                params=request.query_params,
            )
            response_headers = {}
            for key, value in resp.headers.items():
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="ignore")
                response_headers[key] = value
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=response_headers,
            )
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            raise HTTPException(503, f"Service unavailable: {str(e)}")

# === Настройка OpenAPI (Swagger) ===
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="API Gateway",
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"]:
        if path != "/health":
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [
                    {"BearerAuth": []}
                ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi