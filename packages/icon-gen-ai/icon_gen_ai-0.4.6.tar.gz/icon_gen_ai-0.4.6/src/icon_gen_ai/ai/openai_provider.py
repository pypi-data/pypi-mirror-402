"""OpenAI LLM provider implementation."""

import json
from typing import Optional, Dict, Any, List

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .base import BaseLLMProvider, LLMResponse, IconSuggestion


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider for icon suggestions."""
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            base_url: Optional custom base URL (for enterprise/Azure deployments)
            model: Model to use (default: gpt-4o-mini for cost efficiency)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. Install it with: pip install openai"
            )
        
        super().__init__(api_key, base_url, model, max_tokens, temperature)
        
        # Initialize OpenAI client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = openai.OpenAI(**client_kwargs)
    
    def get_default_model(self) -> str:
        """Return the default OpenAI model."""
        return "gpt-4o-mini"  # Cost-effective choice
    
    def get_provider_name(self) -> str:
        """Return provider name."""
        return "openai"
    
    def is_available(self) -> bool:
        """Check if OpenAI is available and configured."""
        if not OPENAI_AVAILABLE:
            return False
        
        try:
            # Quick test to see if API key works
            self.client.models.list()
            return True
        except Exception:
            return False
    
    def query(
        self,
        user_prompt: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Query OpenAI with a prompt.
        
        Args:
            user_prompt: User's icon request
            system_prompt: System instructions
            context: Additional context
            
        Returns:
            LLMResponse with suggestions
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Add context if provided
            if context:
                context_str = f"\nAdditional context: {json.dumps(context, indent=2)}"
                messages[-1]["content"] += context_str
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}  # Request JSON response
            )
            
            # Extract response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Parse JSON response
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback to text parsing if JSON fails
                return self._parse_text_response(content, tokens_used)
            
            # Build IconSuggestion objects
            suggestions = []
            for item in data.get("suggestions", []):
                style_suggestions = item.get("style_suggestions")
                
                suggestions.append(IconSuggestion(
                    icon_name=item.get("icon_name", ""),
                    reason=item.get("reason", ""),
                    use_case=item.get("use_case", ""),
                    confidence=item.get("confidence", 0.8),
                    style_suggestions=style_suggestions
                ))
            
            return LLMResponse(
                suggestions=suggestions,
                explanation=data.get("explanation", ""),
                search_query=data.get("search_query", user_prompt),
                tokens_used=tokens_used,
                provider=self.get_provider_name()
            )
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _parse_text_response(self, text: str, tokens_used: int) -> LLMResponse:
        """Fallback parser for non-JSON responses."""
        suggestions = self.parse_icon_suggestions(text)
        
        return LLMResponse(
            suggestions=suggestions,
            explanation=text[:200],  # First 200 chars as explanation
            search_query="parsed from text",
            tokens_used=tokens_used,
            provider=self.get_provider_name()
        )
    
    def estimate_cost(self, tokens_used: int) -> float:
        """Estimate OpenAI API cost.
        
        Based on gpt-4o-mini pricing (as of 2024):
        - Input: $0.150 per 1M tokens
        - Output: $0.600 per 1M tokens
        
        Args:
            tokens_used: Total tokens (input + output)
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimate: assume 60% input, 40% output
        input_tokens = tokens_used * 0.6
        output_tokens = tokens_used * 0.4
        
        input_cost = (input_tokens / 1_000_000) * 0.150
        output_cost = (output_tokens / 1_000_000) * 0.600
        
        return input_cost + output_cost