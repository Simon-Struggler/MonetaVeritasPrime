import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./frontend.db")
    GATEWAY_URL: str = os.getenv("GATEWAY_URL", "http://localhost:8000")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_in_production")

settings = Settings()
