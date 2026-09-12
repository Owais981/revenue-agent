from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Revenue Agent"
    environment: str = "development"

    database_url: str = "sqlite:///./revenue_agent.db"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    min_project_value: float = 1000
    proposal_threshold: float = 75
    nurture_threshold: float = 45
    confidence_threshold: float = 0.65

    fit_weight: float = 0.35
    intent_weight: float = 0.40
    deliverability_weight: float = 0.25

    frontend_url: str = "http://localhost:5173"


settings = Settings()
