from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    api_key: str
    jwt_secret: str          # new
    jwt_algorithm: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()