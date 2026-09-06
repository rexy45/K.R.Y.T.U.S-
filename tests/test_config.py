from krytus.config import config


def test_config_loads():
    assert config.OPENAI_API_KEY == "test-key"
    assert config.OPENAI_MODEL == "gpt-4o"
    assert config.TELEGRAM_BOT_TOKEN == "test-token"
    assert config.MY_TELEGRAM_CHAT_ID == 123456789
    assert config.SMTP_HOST == "smtp.gmail.com"
    assert config.TTS_VOICE == "en-US-AriaNeural"
    assert config.TTS_RATE == "+0%"
    assert config.TTS_VOLUME == "+0%"


def test_config_ensure_data_dirs(temp_dirs):
    config.ensure_data_dirs()
    from pathlib import Path
    assert Path(config.CHROMA_DB_PATH).exists()
    assert Path(config.SQLITE_DB_PATH).parent.exists()