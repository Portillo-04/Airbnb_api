import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "airbnb")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "root")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: str = os.getenv("DATABASE_PORT", "3306")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "clave_secreta_default_123")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    APP_NAME: str = os.getenv("APP_NAME", "API Alquileres")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"


settings = Settings()


def get_settings():
    return settings
