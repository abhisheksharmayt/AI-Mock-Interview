from pydantic_settings import BaseSettings
import os


class Configs(BaseSettings):

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "default_secret_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    S3_RESUME_BUCKET: str = "ai-interview-test"


configs = Configs()
