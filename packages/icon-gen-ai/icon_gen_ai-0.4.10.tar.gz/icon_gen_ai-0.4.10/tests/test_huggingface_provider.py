"""Tests for Hugging Face provider with mocked API calls."""

import pytest
from unittest.mock import patch, MagicMock
from icon_gen_ai.ai.huggingface_provider import HuggingFaceProvider
from icon_gen_ai.ai.base import IconSuggestion


class TestHuggingFaceProvider:
    """Test Hugging Face provider functionality with mocked API."""

    def test_initialization_with_token(self):
        """Test provider initialization with HF token."""
        provider = HuggingFaceProvider(api_key="test-token")
        assert provider.api_key == "test-token"
        assert provider.model == "deepseek-ai/DeepSeek-V3.1"

    def test_initialization_custom_model(self):
        """Test provider initialization with custom model."""
        provider = HuggingFaceProvider(
            api_key="test-token",
            model="meta-llama/Llama-3.3-70B-Instruct"
        )
        assert provider.model == "meta-llama/Llama-3.3-70B-Instruct"

    def test_provider_name(self):
        """Test provider name method."""
        provider = HuggingFaceProvider(api_key="test-token")
        assert provider.get_provider_name() == "huggingface"

    @patch('icon_gen_ai.ai.huggingface_provider.InferenceClient')
    def test_discover_icons_success(self, mock_hf_client):
        """Test successful icon discovery with JSON response."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''{
            "suggestions": [
                {
                    "icon_name": "mdi:database",
                    "reason": "Database icon"
                },
                {
                    "icon_name": "heroicons:database",
                    "reason": "Modern database icon"
                }
            ]
        }'''
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 100
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_hf_client.return_value = mock_client_instance
        
        provider = HuggingFaceProvider(api_key="test-token")
        result = provider.query("database icon", system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 2
        assert result.suggestions[0].icon_name == "mdi:database"
        assert result.suggestions[0].reason == "Database icon"
        assert result.suggestions[1].icon_name == "heroicons:database"

    @patch('icon_gen_ai.ai.huggingface_provider.InferenceClient')
    def test_discover_icons_with_context(self, mock_hf_client):
        """Test icon discovery with additional context."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''{
            "suggestions": [{"icon_name": "mdi:cloud", "reason": "Cloud storage"}]
        }'''
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 100
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_hf_client.return_value = mock_client_instance
        
        provider = HuggingFaceProvider(api_key="test-token")
        context = {"design_style": "minimal", "project_type": "cloud"}
        result = provider.query("storage", context=context, system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 1
        # Verify context was passed in the API call
        call_args = mock_client_instance.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = next(m['content'] for m in messages if m['role'] == 'user')
        assert 'minimal' in user_message
        assert 'cloud' in user_message

    @patch('icon_gen_ai.ai.huggingface_provider.InferenceClient')
    def test_discover_icons_text_fallback(self, mock_hf_client):
        """Test fallback to text parsing when JSON fails."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Return non-JSON response that will cause an error
        mock_response.choices[0].message.content = '''
        Icon suggestions:
        1. mdi:code - Code icon
        2. devicon:python - Python icon
        '''
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 100
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_hf_client.return_value = mock_client_instance
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        # Non-JSON responses should raise an exception
        with pytest.raises(Exception):
            provider.query("python icon", system_prompt="You are an icon search assistant")

    @patch('icon_gen_ai.ai.huggingface_provider.InferenceClient')
    def test_discover_icons_api_error(self, mock_hf_client):
        """Test handling of API errors."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.side_effect = Exception("API Error")
        mock_hf_client.return_value = mock_client_instance
        
        provider = HuggingFaceProvider(api_key="test-token")
        
        with pytest.raises(Exception):
            provider.query("test icon", system_prompt="You are an icon search assistant")

    @patch('icon_gen_ai.ai.huggingface_provider.InferenceClient')
    def test_discover_icons_empty_response(self, mock_hf_client):
        """Test handling of empty API response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"suggestions": []}'
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 100
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_hf_client.return_value = mock_client_instance
        
        provider = HuggingFaceProvider(api_key="test-token")
        result = provider.query("nonexistent icon", system_prompt="You are an icon search assistant")
        
        assert len(result.suggestions) == 0

    @patch('icon_gen_ai.ai.huggingface_provider.InferenceClient')
    def test_discover_icons_with_max_tokens(self, mock_hf_client):
        """Test API call includes max_tokens parameter."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"suggestions": []}'
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 100
        
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_hf_client.return_value = mock_client_instance
        
        provider = HuggingFaceProvider(api_key="test-token")
        provider.query("test", system_prompt="You are an icon search assistant")
        
        # Verify max_tokens was passed (HuggingFace uses 10000 tokens)
        call_args = mock_client_instance.chat.completions.create.call_args
        assert 'max_tokens' in call_args[1]
        assert call_args[1]['max_tokens'] == 10000
