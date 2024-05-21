from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    kokomemo_debug: bool = False
    app_name: str = "kokomemo"
    mongodb_url: str = "mongodb://localhost:27017"
    dbname: str = app_name
    logfile: str | None = None
    loglevel: str = "INFO"
    # Secret key for JWT signing- I recommend 512bit or larger!
    secret: str | None = None
    google_id: str | None = None
    # Access Token TTL: 30 minutes
    access_ttl: int = 1800
    # Refresh Token TTL: 1 week
    refresh_ttl: int = 604800

    model_config = SettingsConfigDict(env_file=".env")


config = Settings()


def get_config() -> Settings:
    return config
