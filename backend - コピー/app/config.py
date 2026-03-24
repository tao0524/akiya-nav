from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str

    # Database
    database_url: str = "postgresql://akiya:akiya_pass@localhost:5432/akiya_nav"

    # RAG設定
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o"
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5

    # アプリ設定
    app_name: str = "地域創生AIナビ API"
    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
