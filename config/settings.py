"""
Centralized application settings.

All configuration is loaded from environment variables (via .env file).
This follows the 12-factor app principle and keeps secrets out of the code.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# Root of the project (eleva/)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Application settings.

    Values are automatically loaded from environment variables
    or from the .env file located at the project root.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ignore unknown env variables
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_env: str = Field(default="development", description="Environment: development | staging | production")
    log_level: str = Field(default="INFO", description="Logging level")
    default_company_id: str = Field(default="company_001", description="Default company for testing")

    # ------------------------------------------------------------------
    # Groq LLM
    # ------------------------------------------------------------------
    groq_api_key: str = Field(..., description="Groq API key (required)")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model to use"
    )

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    data_dir: Path = Field(
        default=BASE_DIR / "data" / "sample_data",
        description="Directory containing company private data"
    )
    knowledge_dir: Path = Field(
        default=BASE_DIR / "knowledge" / "playbooks",
        description="Directory containing marketing playbooks (YAML)"
    )
    chroma_persist_dir: Path = Field(
        default=BASE_DIR / "chroma_db",
        description="Local directory for Chroma persistence"
    )

    # Helpers
    
    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


# Singleton instance – import this everywhere
settings = Settings()
