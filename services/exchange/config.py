import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./exchange.db")
    CATALOG_SERVICE_URL: str = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8002")
    COLLECTIONS_SERVICE_URL: str = os.getenv("COLLECTIONS_SERVICE_URL", "http://localhost:8003")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_in_production")
    ALGORITHM: str = "HS256"

settings = Settings()
