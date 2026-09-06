import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "krytus"))

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("MY_TELEGRAM_CHAT_ID", "123456789")
os.environ.setdefault("SMTP_HOST", "smtp.gmail.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USERNAME", "test@gmail.com")
os.environ.setdefault("SMTP_PASSWORD", "test-password")
os.environ.setdefault("EMAIL_FROM", "test@gmail.com")
os.environ.setdefault("CHROMA_DB_PATH", "./test_data/chromadb")
os.environ.setdefault("SQLITE_DB_PATH", "./test_data/krytus.db")
os.environ.setdefault("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("TTS_VOICE", "en-US-AriaNeural")
os.environ.setdefault("TTS_RATE", "+0%")
os.environ.setdefault("TTS_VOLUME", "+0%")


@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        chroma_path = Path(tmpdir) / "chromadb"
        sqlite_path = Path(tmpdir) / "krytus.db"
        chroma_path.mkdir(parents=True, exist_ok=True)
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        
        with patch.dict(os.environ, {
            "CHROMA_DB_PATH": str(chroma_path),
            "SQLITE_DB_PATH": str(sqlite_path),
        }):
            from krytus.config import config
            config.CHROMA_DB_PATH = str(chroma_path)
            config.SQLITE_DB_PATH = str(sqlite_path)
            yield tmpdir


@pytest.fixture
def mock_smtp():
    with patch("krytus.tools.aiosmtplib.send", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_edge_tts():
    with patch("krytus.tools.edge_tts.Communicate") as mock:
        mock_instance = MagicMock()
        
        async def mock_stream():
            yield {"type": "audio", "data": b"fake_audio_data"}
        
        mock_instance.stream = mock_stream
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_bot_app():
    with patch("krytus.tools._bot_application") as mock:
        mock_bot = MagicMock()
        mock_bot.send_voice = AsyncMock()
        mock_bot.send_message = AsyncMock()
        mock.bot = mock_bot
        yield mock


@pytest.fixture(autouse=True)
def reset_singletons():
    import krytus.agent
    import krytus.memory
    import krytus.tools
    krytus.memory._chroma_client = None
    krytus.memory._memory_collection = None
    krytus.tools._bot_application = None
    krytus.agent.agent._provider = None
    yield
    krytus.memory._chroma_client = None
    krytus.memory._memory_collection = None
    krytus.tools._bot_application = None
    krytus.agent.agent._provider = None