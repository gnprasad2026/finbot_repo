from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "openai/gpt-oss-20b"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_HOST_PORT: int = 6333
    QDRANT_URL: str
    QDRANT_API_KEY: str

    # SerpAPI
    SERP_API_KEY: str

    # SQLite
    SQLITE_DB_PATH: str


# Singleton instance — import this wherever you need settings
settings = Settings()
