import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Provider Selection
    LLM_PROVIDER: str = "gemini"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # Google Gemini
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    TELEGRAM_BOT_TOKEN: str
    MY_TELEGRAM_CHAT_ID: int
    TELEGRAM_API_ID: int = 0
    TELEGRAM_API_HASH: str = ""

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str

    # TTS Configuration (Edge TTS)
    TTS_VOICE: str = "en-US-AriaNeural"
    TTS_RATE: str = "+0%"
    TTS_VOLUME: str = "+0%"

    CHROMA_DB_PATH: str = "./data/chromadb"
    SQLITE_DB_PATH: str = "./data/krytus.db"

    def ensure_data_dirs(self) -> None:
        Path(self.CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)


# Let pydantic_settings load from .env automatically
config = Config()