"""AI-powered icon discovery and generation."""

from .base import BaseLLMProvider, IconSuggestion, LLMResponse
from .assistant import IconAssistant

# Import provider classes (always available as Python modules)
from .openai_provider import OpenAIProvider, OPENAI_AVAILABLE
from .anthropic_provider import AnthropicProvider, ANTHROPIC_AVAILABLE
from .huggingface_provider import HuggingFaceProvider, HUGGINGFACE_AVAILABLE

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
    return OPENAI_AVAILABLE or ANTHROPIC_AVAILABLE or HUGGINGFACE_AVAILABLE


def get_available_providers() -> list:
    """Get list of available LLM providers.
    
    Returns:
        List of provider names that have their required packages installed
    """
    providers = []
    if ANTHROPIC_AVAILABLE:
        providers.append("anthropic")
    if HUGGINGFACE_AVAILABLE:
        providers.append("huggingface")
    if OPENAI_AVAILABLE:
        providers.append("openai")
    return providers