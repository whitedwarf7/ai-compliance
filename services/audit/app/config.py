from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Audit service configuration."""

    # Database
    database_url: str = "postgresql://compliance_user:password@localhost:5432/ai_compliance"

    # Logging
    log_level: str = "INFO"

    # Retention
    log_retention_days: int = 365

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


