from fastapi import FastAPI
from api import catalog, internal
from database import engine, Base
from fastapi.openapi.utils import get_openapi

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Catalog Service")
app.include_router(catalog.router)
app.include_router(internal.router)

@app.get("/health")
def health():
    return {"status": "ok"}



def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Catalog Service",
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
    # Для всех эндпоинтов (кроме health) указываем, что требуется авторизация
    for path in openapi_schema["paths"]:
        if path != "/health":
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi