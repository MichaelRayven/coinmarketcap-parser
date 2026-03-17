from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.example", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(...)
    cmc_api_url: str = "https://coinmarketcap.com/"
    cmc_limit: int = 10
    concurrency: int = 10


settings = Settings()
