import os
import logging
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def load_dspy_config() -> Dict[str, Any]:
    """Loads the dspy_config.yaml file from the package directory."""
    try:
        # dspy_config.yaml is in the same directory as this file (onecoder/dspy_config.yaml)
        current_dir = Path(__file__).parent
        config_path = current_dir / "dspy_config.yaml"

        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        return {}
    except Exception as e:
        logger.warning(f"Failed to load dspy_config.yaml: {e}")
        return {}

def configure_dspy(model_name: Optional[str] = None) -> bool:
    """
    Configures DSPy to work with OneCoder's existing LiteLLM environment or custom configuration.

    Args:
        model_name: Optional override for the model name.

    Returns:
        bool: True if configuration was successful, False otherwise.
    """
    try:
        import dspy
    except ImportError:
        logger.warning("DSPy not installed. Skipping configuration.")
        return False

    try:
        config = load_dspy_config()

        # Determine model
        if not model_name:
            # Check environment, then config default, then fallback
            model_name = os.getenv("DSPY_MODEL") or config.get("default_model") or os.getenv("OPENROUTER_MODEL", "openrouter/gpt-4o")

        logger.info(f"Configuring DSPy with model target: {model_name}")

        # Check if model is defined in config
        model_config = config.get("models", {}).get(model_name)

        if model_config:
            logger.info(f"Found configuration for {model_name} in dspy_config.yaml")
            lm_model = model_config.get("model_name")

            # Allow env override for api_base (important for cloud endpoints)
            api_base = os.getenv("OLLAMA_API_BASE") if "ollama" in lm_model else None
            if not api_base:
                 api_base = model_config.get("api_base")

            # Determine API Key based on provider or fallback
            api_key = None
            if "ollama" in lm_model:
                api_key = os.getenv("OLLAMA_API_KEY")

            if not api_key:
                # Fallback to general keys
                api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY") or ""

            lm = dspy.LM(
                model=lm_model,
                api_key=api_key,
                api_base=api_base
            )
            dspy.configure(lm=lm)
            logger.info(f"DSPy configured with YAML model: {lm_model}")
            return True

        # Fallback to original logic if not in YAML

        # Ensure 'openrouter/' prefix if using OpenRouter but missing prefix
        if "openrouter" in os.getenv("LLM_PROVIDER", "").lower() or os.getenv("OPENROUTER_API_KEY"):
            if not model_name.startswith("openrouter/") and not model_name.startswith("gpt-"):
                 model_name = f"openrouter/{model_name}"

        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")
        api_base = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

        if not api_key:
            logger.warning("No API Key found (OPENROUTER_API_KEY or GEMINI_API_KEY). DSPy will fail if run.")
            return False

        lm = dspy.LM(
            model=model_name,
            api_key=api_key,
            api_base=api_base
        )

        dspy.configure(lm=lm)
        logger.info(f"DSPy configured with legacy/env model: {model_name}")
        return True

    except Exception as e:
        logger.error(f"Failed to configure DSPy: {e}")
        return False

def load_compiled_module(module_path: str, module_instance: 'dspy.Module') -> 'dspy.Module':
    """
    Loads a compiled DSPy module from a JSON file.

    Args:
        module_path: Path to the JSON file containing the compiled program.
        module_instance: An instance of the module class to load parameters into.

    Returns:
        The loaded module instance.
    """
    try:
        import dspy
        if os.path.exists(module_path):
            module_instance.load(module_path)
            logger.info(f"Loaded compiled DSPy module from {module_path}")
        else:
            logger.warning(f"Compiled module not found at {module_path}. Using zero-shot.")
        return module_instance
    except ImportError:
        return module_instance
    except Exception as e:
        logger.error(f"Error loading compiled module: {e}")
        return module_instance
