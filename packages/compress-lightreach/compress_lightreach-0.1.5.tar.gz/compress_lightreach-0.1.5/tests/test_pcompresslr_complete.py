"""
Tests for Pcompresslr complete() method.
"""

import pytest
from unittest.mock import Mock, patch
import os

from pcompresslr import Pcompresslr
from pcompresslr import APIKeyError, RateLimitError, APIRequestError


class TestPcompresslrComplete:
    """Test Pcompresslr complete() method."""
    
    @patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
    @patch('pcompresslr.api_client.PcompresslrAPIClient.complete')
    def test_complete_with_cached_key(self, mock_complete):
        """Test complete() with cached LLM key."""
        # Mock API response
        mock_complete.return_value = {
            "decompressed_response": "Test response",
            "compression_stats": {"compression_enabled": True},
            "llm_stats": {"provider": "openai", "model": "gpt-4"},
            "warnings": []
        }
        
        # Create compressor with cached LLM key
        compressor = Pcompresslr(
            prompt="test prompt",
            model="gpt-4",
            llm_provider="openai",
            llm_api_key="sk-test-key"
        )
        
        # Call complete() without providing key again
        result = compressor.complete()
        
        assert result["decompressed_response"] == "Test response"
        # Verify key was used from cache
        call_args = mock_complete.call_args
        assert call_args[1]["llm_api_key"] == "sk-test-key"
        assert call_args[1]["llm_provider"] == "openai"
    
    @patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
    @patch('pcompresslr.api_client.PcompresslrAPIClient.complete')
    def test_complete_with_provided_key(self, mock_complete):
        """Test complete() with key provided in call."""
        # Mock API response
        mock_complete.return_value = {
            "decompressed_response": "Test response",
            "compression_stats": {"compression_enabled": True},
            "llm_stats": {"provider": "openai"},
            "warnings": []
        }
        
        # Create compressor without LLM key
        compressor = Pcompresslr(
            prompt="test prompt",
            model="gpt-4"
        )
        
        # Call complete() with key
        result = compressor.complete(
            llm_provider="openai",
            llm_api_key="sk-test-key"
        )
        
        assert result["decompressed_response"] == "Test response"
        # Verify key was cached
        assert compressor.llm_provider == "openai"
        assert compressor.llm_api_key == "sk-test-key"
    
    @patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
    def test_complete_without_key(self):
        """Test complete() without LLM key raises error."""
        compressor = Pcompresslr(
            prompt="test prompt",
            model="gpt-4"
        )
        
        with pytest.raises(ValueError, match="LLM provider is required"):
            compressor.complete()
    
    @patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
    @patch('pcompresslr.api_client.PcompresslrAPIClient.complete')
    def test_set_llm_key(self, mock_complete):
        """Test set_llm_key() method."""
        mock_complete.return_value = {
            "decompressed_response": "Test",
            "compression_stats": {},
            "llm_stats": {},
            "warnings": []
        }
        
        compressor = Pcompresslr(prompt="test", model="gpt-4")
        
        # Set LLM key
        compressor.set_llm_key("openai", "sk-test-key")
        
        assert compressor.llm_provider == "openai"
        assert compressor.llm_api_key == "sk-test-key"
        assert compressor.has_llm_key() is True
        
        # Use it
        compressor.complete()
        mock_complete.assert_called_once()
    
    @patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
    def test_clear_llm_key(self):
        """Test clear_llm_key() method."""
        compressor = Pcompresslr(
            prompt="test",
            model="gpt-4",
            llm_provider="openai",
            llm_api_key="sk-test"
        )
        
        assert compressor.has_llm_key() is True
        
        compressor.clear_llm_key()
        
        assert compressor.llm_provider is None
        assert compressor.llm_api_key is None
        assert compressor.has_llm_key() is False
    
    @patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
    @patch('pcompresslr.api_client.PcompresslrAPIClient.complete')
    def test_complete_with_different_prompt(self, mock_complete):
        """Test complete() with different prompt."""
        mock_complete.return_value = {
            "decompressed_response": "New response",
            "compression_stats": {},
            "llm_stats": {},
            "warnings": []
        }
        
        compressor = Pcompresslr(
            prompt="original prompt",
            model="gpt-4",
            llm_provider="openai",
            llm_api_key="sk-test"
        )
        
        # Use different prompt
        result = compressor.complete(prompt="new prompt")
        
        assert result["decompressed_response"] == "New response"
        # Verify new prompt was used
        call_args = mock_complete.call_args
        assert call_args[1]["prompt"] == "new prompt"
    
    @patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
    @patch('pcompresslr.api_client.PcompresslrAPIClient.complete')
    def test_complete_with_anthropic(self, mock_complete):
        """Test complete() with Anthropic."""
        mock_complete.return_value = {
            "decompressed_response": "Claude response",
            "compression_stats": {},
            "llm_stats": {"provider": "anthropic"},
            "warnings": []
        }
        
        compressor = Pcompresslr(
            prompt="test",
            model="claude-3-opus",
            llm_provider="anthropic",
            llm_api_key="sk-ant-test"
        )
        
        result = compressor.complete()
        
        assert result["decompressed_response"] == "Claude response"
        call_args = mock_complete.call_args
        assert call_args[1]["llm_provider"] == "anthropic"
    
    @patch.dict(os.environ, {"PCOMPRESLR_API_KEY": "test-api-key"})
    def test_set_llm_key_invalid_provider(self):
        """Test set_llm_key() with invalid provider."""
        compressor = Pcompresslr(prompt="test", model="gpt-4")
        
        with pytest.raises(ValueError, match="Unsupported provider"):
            compressor.set_llm_key("invalid", "sk-test")

