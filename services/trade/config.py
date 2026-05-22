import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trade.db")
    CATALOG_SERVICE_URL: str = os.getenv("CATALOG_SERVICE_URL", "http://catalog:8002")
    COLLECTIONS_SERVICE_URL: str = os.getenv("COLLECTIONS_SERVICE_URL", "http://localhost:8003")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_in_production")
    ALGORITHM: str = "HS256"

settings = Settings()