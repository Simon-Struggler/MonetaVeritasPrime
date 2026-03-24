from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from config import settings
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
}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway(request: Request, path: str):
    # Определяем целевой сервис
    for prefix, url in SERVICE_MAP.items():
        if path.startswith(prefix):
            target_url = f"{url}/{path}"
            break
    else:
        raise HTTPException(404, "Not found")

    # Формируем заголовки: берём только необходимые, преобразуем в строки
    headers = {}
    for key, value in request.headers.items():
        # Пропускаем host, так как он не нужен для внутреннего запроса
        if key.lower() == "host":
            continue
        # Если значение – байты, декодируем; иначе оставляем как есть
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
                params=request.query_params
            )
            # Возвращаем ответ, также декодируя заголовки, если нужно
            response_headers = {}
            for key, value in resp.headers.items():
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="ignore")
                response_headers[key] = value
            return Response(content=resp.content, status_code=resp.status_code, headers=response_headers)
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            raise HTTPException(503, f"Service unavailable: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}

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
    # Для всех эндпоинтов (включая проксируемые) указываем, что требуется авторизация
    # Но это только для документации, реальная проверка происходит в сервисах
    for path in openapi_schema["paths"]:
        if path != "/health":
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi