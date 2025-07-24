from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid", # Keep this for strict validation, or "ignore" if you have truly extra env vars
        case_sensitive=True, # Environment variables are case-sensitive
    )
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    REDIS_URL: str

    # class Config:
    #     env_file = ".env"


settings = Settings()
