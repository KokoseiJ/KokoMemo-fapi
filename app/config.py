from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_url: str = "mongodb://localhost:27017/"
    db_name: str = "kokomemo"
    secret_key: str = "TESTKEY"
    jwt_algo: str = "HS256"
    google_client_id: str = ""

    model_config = SettingsConfigDict(env_file=".env")
