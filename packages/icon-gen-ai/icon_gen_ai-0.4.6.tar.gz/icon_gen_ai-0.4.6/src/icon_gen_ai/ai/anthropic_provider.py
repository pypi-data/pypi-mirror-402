"""Anthropic Claude LLM provider implementation."""

import json
from typing import Optional, Dict, Any

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import BaseLLMProvider, LLMResponse, IconSuggestion


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider for icon suggestions."""
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            base_url: Optional custom base URL (for enterprise deployments)
            model: Model to use (default: claude-3-5-haiku for cost efficiency)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. Install it with: pip install anthropic"
            )
        
        super().__init__(api_key, base_url, model, max_tokens, temperature)
        
        # Initialize Anthropic client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = anthropic.Anthropic(**client_kwargs)
    
    def get_default_model(self) -> str:
        """Return the default Anthropic model."""
        return "claude-3-5-haiku-20241022"  # Fast and cost-effective
    
    def get_provider_name(self) -> str:
        """Return provider name."""
        return "anthropic"
    
    def is_available(self) -> bool:
        """Check if Anthropic is available and configured."""
        if not ANTHROPIC_AVAILABLE:
            return False
        
        try:
            # Quick test to see if API key works
            # Note: Anthropic doesn't have a simple models.list() endpoint
            # So we just check if the client was created successfully
            return self.client is not None
        except Exception:
            return False
    
    def query(
        self,
        user_prompt: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Query Claude with a prompt.
        
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
            # Build user message
            user_message = user_prompt
            if context:
                user_message += f"\n\nAdditional context: {json.dumps(context, indent=2)}"
            
            # Add JSON format instruction to system prompt
            enhanced_system = system_prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON, no additional text."
            
            # Make API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=enhanced_system,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract response
            content = response.content[0].text
            
            # Count tokens (approximate from usage)
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # Parse JSON response
            try:
                # Clean up response if it has markdown code blocks
                if content.strip().startswith("```"):
                    # Remove markdown code blocks
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]  # Remove ```json
                    elif content.startswith("```"):
                        content = content[3:]  # Remove ```
                    if content.endswith("```"):
                        content = content[:-3]  # Remove trailing ```
                    content = content.strip()
                
                data = json.loads(content)
            except json.JSONDecodeError as e:
                # Fallback to text parsing if JSON fails
                print(f"JSON parsing failed: {e}. Falling back to text parsing.")
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
            raise Exception(f"Anthropic API error: {str(e)}")
    
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
        """Estimate Anthropic API cost.
        
        Based on Claude 3.5 Haiku pricing (as of 2024):
        - Input: $0.80 per 1M tokens
        - Output: $4.00 per 1M tokens
        
        Args:
            tokens_used: Total tokens (input + output)
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimate: assume 60% input, 40% output
        input_tokens = tokens_used * 0.6
        output_tokens = tokens_used * 0.4
        
        input_cost = (input_tokens / 1_000_000) * 0.80
        output_cost = (output_tokens / 1_000_000) * 4.00
        
        return input_cost + output_cost