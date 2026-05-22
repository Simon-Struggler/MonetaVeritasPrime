import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

class Settings(BaseSettings):
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    CATALOG_SERVICE_URL: str = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8002")
    COLLECTIONS_SERVICE_URL: str = os.getenv("COLLECTIONS_SERVICE_URL", "http://localhost:8003")
    MEDIA_SERVICE_URL: str = os.getenv("MEDIA_SERVICE_URL", "http://localhost:8004")
    AUCTION_SERVICE_URL: str = os.getenv("AUCTION_SERVICE_URL", "http://localhost:8005")
    TRADE_SERVICE_URL: str = os.getenv("TRADE_SERVICE_URL", "http://localhost:8006")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_in_production")
    ALGORITHM: str = "HS256"

settings = Settings()