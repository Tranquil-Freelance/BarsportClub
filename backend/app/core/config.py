"""
Application configuration using environment variables.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import computed_field, Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    PROJECT_NAME: str = "xPalermoStat API"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL configuration
    POSTGRES_USER: str = Field(..., description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL password")
    POSTGRES_SERVER: str = Field(..., description="PostgreSQL server host")
    POSTGRES_PORT: str = Field("5432", description="PostgreSQL server port")
    POSTGRES_DB: str = Field(..., description="PostgreSQL database name")

    # ScraperAPI proxy
    SCRAPERAPI_KEY: str = Field(..., description="ScraperAPI key for proxy")

    # The-Odds-API
    ODDS_API_KEY: str = Field("", description="The-Odds-API key for live odds")

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Build the async PostgreSQL connection string.
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()