import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./auction.db")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8004")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_in_production")
    ALGORITHM: str = "HS256"

settings = Settings()
    