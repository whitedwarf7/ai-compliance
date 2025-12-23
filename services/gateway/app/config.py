from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Gateway service configuration."""

    # AI Provider settings
    ai_provider: Literal["openai", "azure"] = "openai"

    # OpenAI settings
    openai_api_key: str = ""

    # Azure OpenAI settings
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"

    # Default model
    default_model: str = "gpt-4o"

    # Audit service
    audit_service_url: str = "http://audit:8001"

    # Logging
    log_level: str = "INFO"

    # Security
    secret_key: str = "change-this-to-a-secure-random-string"

    # PII Detection
    pii_detection_enabled: bool = True
    pii_detection_log_matches: bool = False  # Don't log actual PII values

    # Policy Engine
    policy_file: str = "/app/policies/default.yaml"
    policy_hot_reload: bool = True

    # Enforcement
    enforcement_mode: Literal["enforce", "warn", "log_only"] = "enforce"

    # Alerts - Slack
    alert_slack_webhook: str = ""

    # Alerts - Email
    alert_email_enabled: bool = False
    alert_email_smtp_host: str = ""
    alert_email_smtp_port: int = 587
    alert_email_smtp_user: str = ""
    alert_email_smtp_password: str = ""
    alert_email_from: str = ""
    alert_email_to: str = ""  # Comma-separated list

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def alert_email_recipients(self) -> list[str]:
        """Get email recipients as list."""
        if not self.alert_email_to:
            return []
        return [e.strip() for e in self.alert_email_to.split(",") if e.strip()]


settings = Settings()
