"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class IconSuggestion:
    """Represents a suggested icon from the LLM."""
    
    icon_name: str  # e.g., "simple-icons:openai"
    reason: str  # Why this icon was suggested
    use_case: str  # When to use this icon
    confidence: float = 1.0  # 0.0 to 1.0
    style_suggestions: Optional[Dict[str, Any]] = None  # color, size, bg_color, etc.


@dataclass
class LLMResponse:
    """Represents the complete response from an LLM."""
    
    suggestions: List[IconSuggestion]
    explanation: str  # Overall explanation of the suggestions
    search_query: str  # The interpreted search query
    tokens_used: int = 0  # For cost tracking
    provider: str = "unknown"


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(
        self, 
        api_key: str, 
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """Initialize the LLM provider.
        
        Args:
            api_key: API key for the LLM service
            base_url: Optional custom base URL (for enterprise/custom deployments)
            model: Model name to use (provider-specific)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 to 1.0)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model or self.get_default_model()
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._validate_config()
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model name for this provider."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'anthropic')."""
        pass
    
    def _validate_config(self):
        """Validate the configuration. Raise ValueError if invalid."""
        if not self.api_key:
            raise ValueError(f"{self.get_provider_name()} API key is required")
        
        if self.temperature < 0.0 or self.temperature > 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
    
    @abstractmethod
    def query(
        self, 
        user_prompt: str, 
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Query the LLM with a prompt.
        
        Args:
            user_prompt: The user's request (e.g., "Find icons for payment")
            system_prompt: System instructions for the LLM
            context: Additional context (e.g., previous suggestions, user preferences)
            
        Returns:
            LLMResponse with icon suggestions and metadata
            
        Raises:
            Exception: If the API call fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured correctly.
        
        Returns:
            True if the provider can be used, False otherwise
        """
        pass
    
    def parse_icon_suggestions(self, llm_text: str) -> List[IconSuggestion]:
        """Parse icon suggestions from LLM response text.
        
        This is a helper method that can be overridden by providers if they
        have specific parsing needs. Default implementation looks for common patterns.
        
        Args:
            llm_text: Raw text response from the LLM
            
        Returns:
            List of IconSuggestion objects
        """
        # This is a simple default implementation
        # Providers can override with more sophisticated parsing
        suggestions = []
        
        # Look for patterns like "mdi:icon-name" or "simple-icons:name"
        import re
        pattern = r'([a-z0-9-]+:[a-z0-9-]+)'
        matches = re.findall(pattern, llm_text.lower())
        
        for match in matches:
            suggestions.append(IconSuggestion(
                icon_name=match,
                reason="Suggested by AI",
                use_case="General purpose",
                confidence=0.8
            ))
        
        return suggestions
    
    def estimate_cost(self, tokens_used: int) -> float:
        """Estimate the cost of the API call.
        
        Args:
            tokens_used: Number of tokens used
            
        Returns:
            Estimated cost in USD (0.0 if cost tracking not implemented)
        """
        # Override in specific providers with actual pricing
        return 0.0