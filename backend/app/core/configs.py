from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Configs(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    JWT_SECRET_KEY: str = "default_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    S3_RESUME_BUCKET: str = "ai-interview-test"
    OPENAI_API_KEY: str = "default_openai_api_key"


configs = Configs()
