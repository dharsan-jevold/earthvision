"""
Centralized settings, read from environment variables with sane local
defaults. Nothing here requires the user to set anything to run locally.
"""
import os


class Settings:
    SECRET_KEY: str = os.environ.get("EARTHVISION_SECRET_KEY", "dev-secret-change-in-production")
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite:///./earthvision.db")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


settings = Settings()
