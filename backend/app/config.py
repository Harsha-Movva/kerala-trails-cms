from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./kerala_trails.db"
    jwt_secret: str = "local-development-secret-change-me"
    jwt_expires_minutes: int = 720
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"
    app_env: str = "development"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
