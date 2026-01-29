"""HuggingFace Inference API provider implementation."""

import json
from typing import Optional, Dict, Any

try:
    from huggingface_hub import InferenceClient
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

from .base import BaseLLMProvider, LLMResponse, IconSuggestion


class HuggingFaceProvider(BaseLLMProvider):
    """HuggingFace Inference API provider for icon suggestions."""
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """Initialize HuggingFace provider.
        
        Args:
            api_key: HuggingFace API token
            base_url: Optional custom base URL (for enterprise deployments)
            model: Model to use (default: deepseek-ai/DeepSeek-V3.1)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        """
        if not HUGGINGFACE_AVAILABLE:
            raise ImportError(
                "huggingface_hub package not installed. Install it with: pip install huggingface-hub"
            )
        
        super().__init__(api_key, base_url, model, max_tokens, temperature)
        
        # Initialize HuggingFace client
        self.client = InferenceClient(
            api_key=self.api_key,
            base_url=self.base_url if self.base_url else None
        )
    
    def get_default_model(self) -> str:
        """Return the default HuggingFace model."""
        return "deepseek-ai/DeepSeek-V3.1"# "deepseek-ai/DeepSeek-V3-0324"
    
    def get_provider_name(self) -> str:
        """Return provider name."""
        return "huggingface"
    
    def is_available(self) -> bool:
        """Check if HuggingFace is available and configured."""
        if not HUGGINGFACE_AVAILABLE:
            return False
        
        try:
            # Check if client was created successfully
            return self.client is not None
        except Exception:
            return False
    
    def query(
        self,
        user_prompt: str,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Query HuggingFace model with a prompt.
        
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
            enhanced_system = system_prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON, no additional text or markdown formatting."
            
            # Make API call with sufficient tokens for up to 25 suggestions
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": enhanced_system},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=10000,  # ~400 tokens per suggestion × 25 = 10,000
                temperature=self.temperature
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Strip markdown code fences if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                # Find the end of the first line (```json or just ```)
                first_newline = response_text.find('\n')
                if first_newline > 0:
                    response_text = response_text[first_newline + 1:]
                
                # Remove trailing ```
                if response_text.rstrip().endswith('```'):
                    response_text = response_text.rstrip()[:-3].rstrip()
            
            # Parse JSON response with fallback for incomplete JSON
            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                # Print debug info
                print(f"JSON parsing failed: {e}")
                print(f"Response text (first 200 chars): {response_text[:200]}")
                print(f"Response text (last 200 chars): {response_text[-200:]}")
                
                # Try to fix incomplete JSON by finding the last complete object
                response_json = self._repair_json(response_text)
            
            # Build suggestions
            suggestions = []
            for suggestion_data in response_json.get("suggestions", []):
                suggestion = IconSuggestion(
                    icon_name=suggestion_data.get("icon_name", ""),
                    reason=suggestion_data.get("reason", ""),
                    use_case=suggestion_data.get("use_case", ""),
                    confidence=float(suggestion_data.get("confidence", 1.0)),
                    style_suggestions=suggestion_data.get("style_suggestions")
                )
                suggestions.append(suggestion)
            
            # Return structured response
            return LLMResponse(
                suggestions=suggestions,
                explanation=response_json.get("explanation", ""),
                search_query=response_json.get("search_query", user_prompt),
                tokens_used=getattr(response.usage, "total_tokens", 0) if hasattr(response, "usage") else 0,
                provider=self.get_provider_name()
            )
            
        except Exception as e:
            print(f"Error querying HuggingFace: {e}")
            raise
    
    def _repair_json(self, text: str) -> Dict[str, Any]:
        """Attempt to repair truncated/incomplete JSON.
        
        Args:
            text: Potentially incomplete JSON string
            
        Returns:
            Parsed JSON dictionary with what we could recover
        """
        text = text.rstrip()
        
        # Check if response is completely empty or not JSON at all
        if not text or not text.strip().startswith('{'):
            print(f"ERROR: Response doesn't look like JSON. Full text:\n{text}")
            raise json.JSONDecodeError(
                "Response is not valid JSON format",
                text,
                0
            )
        
        # Find the position of the suggestions array start
        suggestions_start = text.find('"suggestions"')
        if suggestions_start == -1:
            print(f"ERROR: No 'suggestions' field found in response")
            raise json.JSONDecodeError(
                "No suggestions array found in response",
                text,
                0
            )
        
        # Find the '[' that starts the array
        array_start = text.find('[', suggestions_start)
        if array_start == -1:
            raise json.JSONDecodeError(
                "Suggestions array not properly opened",
                text,
                0
            )
        
        # Find the last complete suggestion object by looking for '},' or '}]'
        # Work backwards from the end to find the last complete suggestion
        last_complete_suggestion = -1
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i in range(len(text) - 1, array_start, -1):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and (i == 0 or text[i-1] != '\\'):
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            if char == '}':
                brace_count += 1
                if brace_count == 1:
                    # Found a closing brace for a suggestion
                    last_complete_suggestion = i + 1
            elif char == '{':
                brace_count -= 1
                if brace_count == 0 and last_complete_suggestion > 0:
                    # Found the opening brace matching our last complete suggestion
                    break
        
        # If we found a complete suggestion, truncate and close the JSON
        if last_complete_suggestion > 0:
            try:
                # Check if there's a comma after the suggestion (incomplete next suggestion)
                after_suggestion = text[last_complete_suggestion:last_complete_suggestion+10]
                if after_suggestion.lstrip().startswith(','):
                    # There's another incomplete suggestion, just close the array
                    truncated = text[:last_complete_suggestion] + ']}'
                else:
                    truncated = text[:last_complete_suggestion] + ']}'
                
                partial = json.loads(truncated)
                
                # Ensure suggestions array exists
                if "suggestions" not in partial:
                    partial["suggestions"] = []
                
                print("Warning: Truncated response from HuggingFace, recovered partial data")
                return partial
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to just close the structure as-is
        try:
            # Try to find where the suggestions array ends and close there
            truncated = text.rstrip()
            if truncated.endswith(','):
                truncated = truncated[:-1]
            
            # Count brackets to find correct closing
            open_braces = truncated.count('{') - truncated.count('}')
            open_brackets = truncated.count('[') - truncated.count(']')
            
            truncated += ']' * max(1, open_brackets) + '}' * max(1, open_braces)
            partial = json.loads(truncated)
            return partial
        except json.JSONDecodeError:
            pass
        
        # If repair fails, raise error with original message
        raise json.JSONDecodeError(
            "Unable to parse or repair JSON from HuggingFace response",
            text,
            0
        )
