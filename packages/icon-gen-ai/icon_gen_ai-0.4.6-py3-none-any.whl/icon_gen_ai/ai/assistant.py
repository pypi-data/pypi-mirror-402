"""Main AI assistant for icon discovery and generation."""

import os
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load from .env file in current directory
    # Also try parent directories for workspace-level .env
    load_dotenv(Path.cwd().parent / '.env')
except ImportError:
    # python-dotenv not installed, will use system environment variables only
    pass

from .base import BaseLLMProvider, LLMResponse, IconSuggestion
from .prompts import (
    ICON_DISCOVERY_SYSTEM_PROMPT,
    get_enhanced_prompt,
    get_style_recommendations
)


class IconAssistant:
    """AI-powered assistant for icon discovery and generation."""
    
    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        cache_dir: Optional[str] = None,
        enable_caching: bool = True
    ):
        """Initialize the Icon Assistant.
        
        Args:
            provider: LLM provider instance. If None, will auto-detect from environment
            cache_dir: Directory for caching responses (default: ~/.icon-gen/cache)
            enable_caching: Whether to cache LLM responses
        """
        self.provider = provider or self._auto_detect_provider()
        self.enable_caching = enable_caching
        self.cache_dir = Path(cache_dir or Path.home() / ".icon-gen" / "cache")
        self.cache: Dict[str, LLMResponse] = {}
        
        if self.enable_caching:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _auto_detect_provider(self) -> Optional[BaseLLMProvider]:
        """Auto-detect and initialize an LLM provider from environment variables.
        
        Checks in order:
        1. ANTHROPIC_API_KEY
        2. OPENAI_API_KEY
        3. HUGGINGFACE_API_TOKEN
        
        Returns:
            Initialized provider or None if no credentials found
        """
        # Try Anthropic first
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        anthropic_base = os.getenv("ANTHROPIC_BASE_URL")
        
        if anthropic_key:
            try:
                from .anthropic_provider import AnthropicProvider
                return AnthropicProvider(
                    api_key=anthropic_key,
                    base_url=anthropic_base
                )
            except ImportError:
                print("Warning: anthropic package not installed")
        
        # Try OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_base = os.getenv("OPENAI_BASE_URL")
        
        if openai_key:
            try:
                from .openai_provider import OpenAIProvider
                return OpenAIProvider(
                    api_key=openai_key,
                    base_url=openai_base
                )
            except ImportError:
                print("Warning: openai package not installed")
        
        # Try HuggingFace
        huggingface_key = os.getenv("HUGGINGFACE_API_TOKEN")
        huggingface_base = os.getenv("HUGGINGFACE_BASE_URL")
        
        if huggingface_key:
            try:
                from .huggingface_provider import HuggingFaceProvider
                return HuggingFaceProvider(
                    api_key=huggingface_key,
                    base_url=huggingface_base
                )
            except ImportError:
                print("Warning: huggingface_hub package not installed")
        
        # No provider found
        return None
    
    def is_available(self) -> bool:
        """Check if AI features are available.
        
        Returns:
            True if an LLM provider is configured and available
        """
        if self.provider is None:
            return False
        return self.provider.is_available()
    
    def _get_cache_key(self, query: str, context: Optional[Dict] = None) -> str:
        """Generate a cache key for a query."""
        import hashlib
        cache_str = query
        if context:
            cache_str += str(sorted(context.items()))
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[LLMResponse]:
        """Get response from cache."""
        if not self.enable_caching:
            return None
        
        # Check in-memory cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                import json
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Reconstruct LLMResponse
                suggestions = [
                    IconSuggestion(**s) for s in data.get('suggestions', [])
                ]
                response = LLMResponse(
                    suggestions=suggestions,
                    explanation=data.get('explanation', ''),
                    search_query=data.get('search_query', ''),
                    tokens_used=data.get('tokens_used', 0),
                    provider=data.get('provider', 'cached')
                )
                
                # Store in memory
                self.cache[cache_key] = response
                return response
            except Exception as e:
                print(f"Warning: Failed to load cache: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, response: LLMResponse):
        """Save response to cache."""
        if not self.enable_caching:
            return
        
        # Save to memory
        self.cache[cache_key] = response
        
        # Save to disk
        try:
            import json
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            # Convert to dict
            data = {
                'suggestions': [
                    {
                        'icon_name': s.icon_name,
                        'reason': s.reason,
                        'use_case': s.use_case,
                        'confidence': s.confidence,
                        'style_suggestions': s.style_suggestions
                    }
                    for s in response.suggestions
                ],
                'explanation': response.explanation,
                'search_query': response.search_query,
                'tokens_used': response.tokens_used,
                'provider': response.provider
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")
    
    def discover_icons(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> LLMResponse:
        """Discover icons based on a natural language query.
        
        Args:
            query: Natural language description (e.g., "5 payment icons for checkout")
            context: Optional context (project_type, design_style, etc.)
            use_cache: Whether to use cached results
            
        Returns:
            LLMResponse with icon suggestions
            
        Raises:
            RuntimeError: If no LLM provider is available
        """
        if not self.is_available():
            raise RuntimeError(
                "No LLM provider available. Please set OPENAI_API_KEY, ANTHROPIC_API_KEY, "
                "or HUGGINGFACE_API_TOKEN environment variable, or pass a provider explicitly."
            )
        
        # Check cache
        cache_key = self._get_cache_key(query, context)
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                print(f"Using cached response (saved {cached.tokens_used} tokens)")
                return cached
        
        # Build enhanced prompt
        enhanced_query = get_enhanced_prompt(query, context)
        
        # Query LLM
        print(f"Querying Iconify using {self.provider.get_provider_name()} (model: {self.provider.model})...")

        response = self.provider.query(
            user_prompt=enhanced_query,
            system_prompt=ICON_DISCOVERY_SYSTEM_PROMPT,
            context=context
        )
        
        # Display cost estimate
        cost = self.provider.estimate_cost(response.tokens_used)
        print(f"Used {response.tokens_used} tokens (≈${cost:.4f})")
        
        # Cache the response
        if use_cache:
            self._save_to_cache(cache_key, response)
        
        return response
    
    
    def get_style_advice(self, style: str) -> Dict[str, Any]:
        """Get style recommendations for a design style.
        
        Args:
            style: Design style (modern, corporate, minimal, playful)
            
        Returns:
            Dictionary with style recommendations
        """
        return get_style_recommendations(style)
    
    def clear_cache(self):
        """Clear the response cache."""
        self.cache.clear()
        
        if self.cache_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                print("Cache cleared successfully")
            except Exception as e:
                print(f"Error clearing cache: {e}")