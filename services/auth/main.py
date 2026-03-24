from fastapi import FastAPI
from api import auth
from database import engine, Base
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.openapi.utils import get_openapi

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service")
app.include_router(auth.router)

@app.get("/health")
def health():
    return {"status": "ok"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Включим в OpenAPI схему безопасности
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Auth Service",
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
    # Указываем, что все эндпоинты (кроме auth) требуют авторизацию
    for path in openapi_schema["paths"]:
        if not path.startswith("/auth"):
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi