from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "kokomemo"
    mongodb_url: str = "mongodb://localhost:27017"
    dbname: str = app_name
    logfile: str = None
    loglevel: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")


config = Settings()
