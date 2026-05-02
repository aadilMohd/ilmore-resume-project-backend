from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENVIRONMENT: str = "dev"
    DATABASE_URL: str 
    GEMINI_API_KEY: str
    CLAUDE_API_KEY: str
    REDIS_URL: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    GOOGLE_CLIENT_ID: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()