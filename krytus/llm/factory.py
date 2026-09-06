from krytus.config import config
from krytus.llm.base import LLMProvider
from krytus.llm.gemini_provider import GeminiProvider
from krytus.llm.openai_provider import OpenAIProvider


def get_llm_provider() -> LLMProvider:
    provider = config.LLM_PROVIDER.lower()
    
    if provider == "gemini":
        if not config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY required for Gemini provider")
        return GeminiProvider(
            api_key=config.GOOGLE_API_KEY,
            model=config.GEMINI_MODEL,
        )
    elif provider == "openai":
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required for OpenAI provider")
        return OpenAIProvider(
            api_key=config.OPENAI_API_KEY,
            model=config.OPENAI_MODEL,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'openai' or 'gemini'")