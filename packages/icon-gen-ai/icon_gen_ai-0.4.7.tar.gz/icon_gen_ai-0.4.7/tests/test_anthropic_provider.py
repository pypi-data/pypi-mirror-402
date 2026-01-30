"""Tests for Anthropic provider with mocked API calls."""

import pytest
from unittest.mock import MagicMock, patch
from icon_gen_ai.ai.anthropic_provider import AnthropicProvider
from icon_gen_ai.ai.base import LLMResponse


class TestAnthropicProvider:
    """Test suite for AnthropicProvider with mocked API."""
    
    @patch('anthropic.Anthropic')
    def test_initialization_with_api_key(self, mock_anthropic):
        """Test provider initialization with API key."""
        provider = AnthropicProvider(api_key="test-key")
        
        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-5-haiku-20241022"
        assert provider.get_provider_name() == "anthropic"
        mock_anthropic.assert_called_once_with(api_key="test-key")
    
    @patch('anthropic.Anthropic')
    def test_initialization_custom_model(self, mock_anthropic):
        """Test provider initialization with custom model."""
        provider = AnthropicProvider(
            api_key="test-key",
            model="claude-3-5-sonnet-20241022"
        )
        
        assert provider.model == "claude-3-5-sonnet-20241022"
    
    @patch('anthropic.Anthropic')
    def test_provider_name(self, mock_anthropic):
        """Test that provider returns correct name."""
        provider = AnthropicProvider(api_key="test-key")
        assert provider.get_provider_name() == "anthropic"
    
    @patch('anthropic.Anthropic')
    def test_query_success(self, mock_anthropic):
        """Test successful icon discovery with JSON response."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '''{
            "suggestions": [
                {
                    "icon_name": "mdi:database",
                    "reason": "Database icon",
                    "use_case": "For database features",
                    "confidence": 0.9
                },
                {
                    "icon_name": "heroicons:database",
                    "reason": "Modern database icon",
                    "use_case": "For modern UI",
                    "confidence": 0.85
                }
            ],
            "explanation": "Database related icons",
            "search_query": "database"
        }'''
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 100
        
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client_instance
        
        provider = AnthropicProvider(api_key="test-key")
        result = provider.query("database icon", system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 2
        assert result.suggestions[0].icon_name == "mdi:database"
        assert result.suggestions[0].reason == "Database icon"
        assert result.suggestions[0].confidence == 0.9
        assert result.suggestions[1].icon_name == "heroicons:database"
        assert result.tokens_used == 150  # 50 input + 100 output
        assert result.provider == "anthropic"
    
    @patch('anthropic.Anthropic')
    def test_query_with_context(self, mock_anthropic):
        """Test icon discovery with additional context."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '''{
            "suggestions": [{"icon_name": "mdi:cloud", "reason": "Cloud storage"}]
        }'''
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 30
        mock_response.usage.output_tokens = 50
        
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client_instance
        
        provider = AnthropicProvider(api_key="test-key")
        context = {"design_style": "minimal", "project_type": "cloud"}
        result = provider.query("storage", context=context, system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 1
        # Verify context was passed in the API call
        call_args = mock_client_instance.messages.create.call_args
        messages = call_args[1]['messages']
        user_message = messages[0]['content']
        assert 'minimal' in user_message
        assert 'cloud' in user_message
    
    @patch('anthropic.Anthropic')
    def test_query_with_markdown_code_blocks(self, mock_anthropic):
        """Test handling of response with markdown code blocks."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '''```json
{
    "suggestions": [{"icon_name": "mdi:code", "reason": "Code icon"}]
}
```'''
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 20
        mock_response.usage.output_tokens = 30
        
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client_instance
        
        provider = AnthropicProvider(api_key="test-key")
        result = provider.query("code icon", system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 1
        assert result.suggestions[0].icon_name == "mdi:code"
    
    @patch('anthropic.Anthropic')
    def test_query_text_fallback(self, mock_anthropic):
        """Test fallback to text parsing when JSON fails."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        # Return non-JSON response
        mock_response.content[0].text = '''
        Icon suggestions:
        1. mdi:code - Code icon
        2. devicon:python - Python icon
        '''
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 25
        mock_response.usage.output_tokens = 40
        
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client_instance
        
        provider = AnthropicProvider(api_key="test-key")
        result = provider.query("python icon", system_prompt="You are an icon search assistant")
        
        # Should fall back to text parsing
        assert len(result.suggestions) >= 1
        assert result.tokens_used == 65
        assert result.provider == "anthropic"
    
    @patch('anthropic.Anthropic')
    def test_query_api_error(self, mock_anthropic):
        """Test handling of API errors."""
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client_instance
        
        provider = AnthropicProvider(api_key="test-key")
        
        with pytest.raises(Exception) as exc_info:
            provider.query("test icon", system_prompt="You are an icon search assistant")
        
        assert "Anthropic API error" in str(exc_info.value)
    
    @patch('anthropic.Anthropic')
    def test_query_empty_response(self, mock_anthropic):
        """Test handling of empty API response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"suggestions": []}'
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 15
        
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client_instance
        
        provider = AnthropicProvider(api_key="test-key")
        result = provider.query("nonexistent icon", system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 0
        assert result.tokens_used == 25
    
    @patch('anthropic.Anthropic')
    def test_query_with_system_prompt(self, mock_anthropic):
        """Test that system prompt is properly passed to API."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"suggestions": []}'
        mock_response.usage = MagicMock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 10
        
        mock_client_instance = MagicMock()
        mock_client_instance.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client_instance
        
        provider = AnthropicProvider(api_key="test-key")
        provider.query("test", system_prompt="Custom system instructions")
        
        # Verify system prompt was passed
        call_args = mock_client_instance.messages.create.call_args
        system_prompt = call_args[1]['system']
        assert 'Custom system instructions' in system_prompt
        assert 'ONLY with valid JSON' in system_prompt
    
    @patch('anthropic.Anthropic')
    def test_estimate_cost(self, mock_anthropic):
        """Test cost estimation for API usage."""
        provider = AnthropicProvider(api_key="test-key")
        
        # Test with 1000 tokens
        cost = provider.estimate_cost(1000)
        
        # 60% input (600 tokens) at $0.80/1M = $0.00048
        # 40% output (400 tokens) at $4.00/1M = $0.0016
        # Total should be around $0.00208
        assert cost > 0
        assert cost < 0.01  # Should be very small for 1000 tokens
    
    @patch('anthropic.Anthropic')
    def test_is_available(self, mock_anthropic):
        """Test availability check."""
        mock_client_instance = MagicMock()
        mock_anthropic.return_value = mock_client_instance
        
        provider = AnthropicProvider(api_key="test-key")
        
        # Should return True when client is initialized
        assert provider.is_available() is True
