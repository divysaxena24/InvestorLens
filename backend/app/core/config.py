
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CLERK_ISSUER: str
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "investorlens_chunks"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
