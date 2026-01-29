"""
Configuration module for AutoEngineer-CLI.
Manages OpenRouter model mappings and system settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Central configuration for the AutoEngineer-CLI system."""
    
    # OpenRouter API Configuration
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    
    # Model Mappings (OpenRouter Free-Tier Models with large context windows)
    # Format: "openrouter/<provider>/<model>:free" for LiteLLM compatibility
    # Using xiaomi/mimo-v2-flash:free (262k context) - less rate-limited
    MANAGER_MODEL = "openrouter/xiaomi/mimo-v2-flash:free"
    ARCHITECT_MODEL = "openrouter/xiaomi/mimo-v2-flash:free"
    CODER_MODEL = "openrouter/mistralai/devstral-2512:free"
    QA_MODEL = "openrouter/nvidia/nemotron-3-nano-30b-a3b:free"
    REVIEWER_MODEL = "openrouter/xiaomi/mimo-v2-flash:free"
    
    # Fallback Models (alternatives if primary fails)
    FALLBACK_MODELS = {
        "manager": "openrouter/arcee-ai/trinity-mini:free",
        "architect": "openrouter/arcee-ai/trinity-mini:free",
        "coder": "openrouter/qwen/qwen3-coder:free",
        "qa": "openrouter/arcee-ai/trinity-mini:free",
        "reviewer": "openrouter/arcee-ai/trinity-mini:free",
    }
    
    # Container Configuration
    PYTHON_CONTAINER_IMAGE = "python:3.11-slim"
    CPP_CONTAINER_IMAGE = "gcc:latest"
    CONTAINER_TIMEOUT = 60  # seconds
    CONTAINER_MEMORY_LIMIT = "512m"
    
    # Retry Configuration
    MAX_QA_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    # Agent Iteration Limits (prevent "Maximum iterations reached")
    AGENT_MAX_ITER = 25  # Max iterations per agent task
    AGENT_MAX_RPM = 10   # Max requests per minute (for rate limiting)
    
    # Output Configuration
    REPORT_FORMAT = "markdown"
    VERBOSE = os.getenv("AUTOENGINEER_VERBOSE", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Get your free API key at https://openrouter.ai/"
            )
        return True
    
    @classmethod
    def get_litellm_config(cls) -> dict:
        """Return configuration dict for LiteLLM API calls."""
        return {
            "api_base": cls.OPENROUTER_BASE_URL,
            "api_key": cls.OPENROUTER_API_KEY,
        }
