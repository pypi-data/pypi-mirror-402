"""AI-powered icon discovery and generation."""

from .base import BaseLLMProvider, IconSuggestion, LLMResponse
from .assistant import IconAssistant

# Optional imports - only load if packages are available
try:
    from .openai_provider import OpenAIProvider
except ImportError:
    OpenAIProvider = None

try:
    from .anthropic_provider import AnthropicProvider
except ImportError:
    AnthropicProvider = None

try:
    from .huggingface_provider import HuggingFaceProvider
except ImportError:
    HuggingFaceProvider = None

__all__ = [
    "IconAssistant",
    "BaseLLMProvider",
    "IconSuggestion",
    "LLMResponse",
    "OpenAIProvider",
    "AnthropicProvider",
    "HuggingFaceProvider",
]


def is_ai_available() -> bool:
    """Check if AI features are available.
    
    Returns:
        True if at least one LLM provider package is installed
    """
    return OpenAIProvider is not None or AnthropicProvider is not None


def get_available_providers() -> list:
    """Get list of available LLM providers.
    
    Returns:
        List of provider names that are available
    """
    providers = []
    if OpenAIProvider is not None:
        providers.append("openai")
    if AnthropicProvider is not None:
        providers.append("anthropic")
    if HuggingFaceProvider is not None:
        providers.append("huggingface")
    return providers