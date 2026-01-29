
import os
from google.adk.models import Gemini, LiteLlm
from dotenv import load_dotenv
from .config_manager import config_manager

def get_model():
    # 1. Check user configuration via config_manager
    model_config = config_manager.get_model_config()
    if model_config and model_config.get("model_name"):
        return LiteLlm(
            model=model_config.get("model_name"),
            api_key=model_config.get("api_key"),
            base_url=model_config.get("base_url"),
        )

    # 2. Priority: Gemini (Default)
    from .env_manager import env_manager
    cwd = os.getcwd()
    
    gemini_api_key = os.getenv("GEMINI_API_KEY") or env_manager.get_env("GEMINI_API_KEY") or env_manager.get_env("GEMINI_API_KEY", cwd)
    if gemini_api_key:
        return Gemini(
            model="gemini-2.0-flash-exp",
            api_key=gemini_api_key
        )

    # 3. Priority: OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY") or env_manager.get_env("OPENAI_API_KEY") or env_manager.get_env("OPENAI_API_KEY", cwd)
    if openai_api_key:
        return LiteLlm(
            model="openai/gpt-4o",
            api_key=openai_api_key
        )

    # 4. Check for OLLAMA_API_KEY (Defaulting to qwen coder)
    ollama_api_key = os.getenv("OLLAMA_API_KEY") or env_manager.get_env("OLLAMA_API_KEY") or env_manager.get_env("OLLAMA_API_KEY", cwd)
    if ollama_api_key:
        base_url = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
        return LiteLlm(
            model="ollama/qwen3-coder:480b-cloud",
            api_key=ollama_api_key,
            base_url=base_url,
        )

    # 5. Fallback to OpenRouter
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY") or env_manager.get_env("OPENROUTER_API_KEY") or env_manager.get_env("OPENROUTER_API_KEY", cwd)
    if openrouter_api_key:
        return LiteLlm(
            model="openrouter/xiaomi/mimo-v2-flash:free",
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    
    raise ValueError(
        "No API key found. Please set GEMINI_API_KEY, OPENAI_API_KEY, OLLAMA_API_KEY, or OPENROUTER_API_KEY, "
        "or configure the model using 'onecoder config model'."
    )
