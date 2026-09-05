from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Narra"
    database_url: str = "sqlite:///./narra.db"
    api_key: str = "narra-dev-key"
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NARRA_", extra="ignore")


settings = Settings()
