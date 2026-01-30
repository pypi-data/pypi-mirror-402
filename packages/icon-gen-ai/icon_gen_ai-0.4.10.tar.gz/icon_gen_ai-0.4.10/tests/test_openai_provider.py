"""Tests for OpenAI provider with mocked API calls."""

import pytest
from unittest.mock import patch, MagicMock
from icon_gen_ai.ai.openai_provider import OpenAIProvider
from icon_gen_ai.ai.base import IconSuggestion


class TestOpenAIProvider:
    """Test OpenAI provider functionality with mocked API."""

    def test_initialization_with_api_key(self):
        """Test provider initialization with API key."""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4o-mini"

    def test_initialization_custom_model(self):
        """Test provider initialization with custom model."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-3.5-turbo")
        assert provider.model == "gpt-3.5-turbo"

    def test_provider_name(self):
        """Test provider name method."""
        provider = OpenAIProvider(api_key="test-key")
        assert provider.get_provider_name() == "openai"

    @patch('openai.OpenAI')
    def test_discover_icons_success(self, mock_openai_client):
        """Test successful icon discovery with JSON response."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''{
            "suggestions": [
                {
                    "icon_name": "mdi:home",
                    "reason": "Simple house icon"
                },
                {
                    "icon_name": "heroicons:home",
                    "reason": "Modern home icon"
                }
            ]
        }'''
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        provider = OpenAIProvider(api_key="test-key")
        result = provider.query("home icon", system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 2
        assert result.suggestions[0].icon_name == "mdi:home"
        assert result.suggestions[0].reason == "Simple house icon"
        assert result.suggestions[1].icon_name == "heroicons:home"

    @patch('openai.OpenAI')
    def test_discover_icons_with_context(self, mock_openai_client):
        """Test icon discovery with additional context."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''{
            "suggestions": [{"icon_name": "mdi:payment", "reason": "Payment icon"}]
        }'''
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        provider = OpenAIProvider(api_key="test-key")
        context = {"design_style": "modern", "project_type": "ecommerce"}
        result = provider.query("payment", context=context, system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 1
        # Verify context was passed in the API call
        call_args = mock_client_instance.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = next(m['content'] for m in messages if m['role'] == 'user')
        assert 'modern' in user_message
        assert 'ecommerce' in user_message

    @patch('openai.OpenAI')
    def test_discover_icons_text_fallback(self, mock_openai_client):
        """Test fallback to text parsing when JSON fails."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Return non-JSON response
        mock_response.choices[0].message.content = '''
        Here are some icons:
        1. mdi:github - GitHub logo
        2. simple-icons:github - Simple GitHub icon
        '''
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        provider = OpenAIProvider(api_key="test-key")
        result = provider.query("github icon", system_prompt="You are an icon search assistant")
        
        # Should fall back to text parsing
        assert len(result.suggestions) >= 1

    @patch('openai.OpenAI')
    def test_discover_icons_api_error(self, mock_openai_client):
        """Test handling of API errors."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_client.return_value = mock_client_instance
        
        provider = OpenAIProvider(api_key="test-key")
        
        with pytest.raises(Exception):
            provider.query("test icon", system_prompt="You are an icon search assistant")

    @patch('openai.OpenAI')
    def test_discover_icons_empty_response(self, mock_openai_client):
        """Test handling of empty API response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"suggestions": []}'
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        provider = OpenAIProvider(api_key="test-key")
        result = provider.query("nonexistent icon", system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 0
