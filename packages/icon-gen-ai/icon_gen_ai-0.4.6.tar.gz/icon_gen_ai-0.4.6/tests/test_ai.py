"""Tests for AI module."""

import pytest
from icon_gen_ai.ai import is_ai_available, get_available_providers


def test_is_ai_available():
    """Test AI availability check."""
    result = is_ai_available()
    assert isinstance(result, bool)


def test_get_available_providers():
    """Test getting available providers."""
    providers = get_available_providers()
    assert isinstance(providers, list)
    # Should be empty if AI not installed, or contain provider names


@pytest.mark.skipif(not is_ai_available(), reason="AI features not installed")
def test_icon_assistant_import():
    """Test IconAssistant can be imported when AI is available."""
    from icon_gen_ai import IconAssistant
    assert IconAssistant is not None


def test_base_llm_provider():
    """Test base LLM provider classes."""
    from icon_gen_ai.ai.base import IconSuggestion, LLMResponse
    
    suggestion = IconSuggestion(
        icon_name='mdi:test',
        reason='Test reason',
        use_case='Testing',
        confidence=0.9
    )
    
    assert suggestion.icon_name == 'mdi:test'
    assert suggestion.confidence == 0.9
    
    response = LLMResponse(
        suggestions=[suggestion],
        explanation='Test explanation',
        search_query='test query',
        tokens_used=100,
        provider='test'
    )
    
    assert len(response.suggestions) == 1
    assert response.tokens_used == 100