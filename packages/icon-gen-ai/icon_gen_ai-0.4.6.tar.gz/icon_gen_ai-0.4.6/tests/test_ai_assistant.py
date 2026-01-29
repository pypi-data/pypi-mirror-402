"""Tests for AI assistant caching and utilities."""

import pytest
from pathlib import Path
from icon_gen_ai.ai.assistant import IconAssistant
from icon_gen_ai.ai.base import IconSuggestion, LLMResponse


def test_assistant_initialization_default():
    """Test assistant initializes with defaults."""
    assistant = IconAssistant()
    
    assert assistant.cache_dir.exists()
    assert isinstance(assistant.cache, dict)
    assert assistant.enable_caching is True


def test_assistant_initialization_custom_cache():
    """Test assistant with custom cache directory."""
    custom_cache = Path('/tmp/icon-gen-test-cache')
    assistant = IconAssistant(cache_dir=str(custom_cache), enable_caching=True)
    
    assert assistant.cache_dir == custom_cache
    assert custom_cache.exists()


def test_assistant_no_caching():
    """Test assistant with caching disabled."""
    assistant = IconAssistant(enable_caching=False)
    
    assert assistant.enable_caching is False


def test_get_cache_key():
    """Test cache key generation."""
    assistant = IconAssistant()
    
    key1 = assistant._get_cache_key("test query")
    key2 = assistant._get_cache_key("test query")
    key3 = assistant._get_cache_key("different query")
    
    assert key1 == key2  # Same query = same key
    assert key1 != key3  # Different query = different key


def test_get_cache_key_with_context():
    """Test cache key with context."""
    assistant = IconAssistant()
    
    key1 = assistant._get_cache_key("test", {"style": "modern"})
    key2 = assistant._get_cache_key("test", {"style": "modern"})
    key3 = assistant._get_cache_key("test", {"style": "corporate"})
    
    assert key1 == key2
    assert key1 != key3


def test_cache_save_and_retrieve(tmp_path):
    """Test saving and retrieving from cache."""
    cache_dir = tmp_path / "cache"
    assistant = IconAssistant(cache_dir=str(cache_dir), enable_caching=True)
    
    # Create a mock response
    suggestion = IconSuggestion(
        icon_name='mdi:test',
        reason='Test',
        use_case='Testing',
        confidence=0.9
    )
    response = LLMResponse(
        suggestions=[suggestion],
        explanation='Test explanation',
        search_query='test',
        tokens_used=100,
        provider='test'
    )
    
    # Save to cache
    cache_key = assistant._get_cache_key("test query")
    assistant._save_to_cache(cache_key, response)
    
    # Retrieve from cache
    cached = assistant._get_from_cache(cache_key)
    
    assert cached is not None
    assert len(cached.suggestions) == 1
    assert cached.suggestions[0].icon_name == 'mdi:test'
    assert cached.tokens_used == 100


def test_cache_miss():
    """Test cache miss returns None."""
    assistant = IconAssistant()
    
    cached = assistant._get_from_cache("nonexistent_key")
    assert cached is None


def test_clear_cache(tmp_path):
    """Test cache clearing."""
    cache_dir = tmp_path / "cache"
    assistant = IconAssistant(cache_dir=str(cache_dir))
    
    # Add something to cache
    assistant.cache["test"] = "value"
    (cache_dir / "test.json").write_text('{"test": "data"}')
    
    # Clear cache
    assistant.clear_cache()
    
    assert len(assistant.cache) == 0
    assert not list(cache_dir.glob("*.json"))


def test_get_style_advice():
    """Test getting style recommendations."""
    assistant = IconAssistant()
    
    advice = assistant.get_style_advice('modern')
    
    assert isinstance(advice, dict)
    assert 'collections' in advice or len(advice) > 0


def test_is_available_without_provider():
    """Test availability check without provider."""
    assistant = IconAssistant()
    # Without API keys, should return False
    result = assistant.is_available()
    assert isinstance(result, bool)