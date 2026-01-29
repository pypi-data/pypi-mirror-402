"""
Tests for the complete endpoint.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from api.main import app
from api.database import get_db
from api.llm.base import LLMResponse, LLMAPIKeyError, LLMRateLimitError, LLMRequestError


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    return db


@pytest.fixture
def mock_api_key():
    """Mock API key record."""
    api_key = Mock()
    api_key.id = 1
    api_key.subscription = Mock()
    api_key.subscription.id = 1
    api_key.subscription.status = "active"
    api_key.subscription.plan = Mock()
    api_key.subscription.plan.allows_greedy = True
    api_key.subscription.plan.allows_optimal = True
    api_key.subscription.plan.tokens_per_month = 1000000
    api_key.subscription.plan.has_full_analytics = False
    api_key.subscription.billing_cycle_end = Mock()
    api_key.subscription.billing_cycle_end.date.return_value = "2024-12-31"
    return api_key


class TestCompleteEndpoint:
    """Test complete endpoint."""
    
    @patch('api.routes.complete.verify_api_key')
    @patch('api.routes.complete.get_db')
    @patch('api.routes.complete.OpenAIClient')
    @patch('api.routes.complete.compress_prompt')
    @patch('api.routes.complete.format_for_llm')
    @patch('api.routes.complete.decompress_llm_format')
    @patch('api.routes.complete.check_token_limit')
    @patch('api.routes.complete.increment_usage')
    def test_complete_with_openai(
        self,
        mock_increment_usage,
        mock_check_token_limit,
        mock_decompress,
        mock_format,
        mock_compress,
        mock_openai_client,
        mock_get_db,
        mock_verify_api_key,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with OpenAI."""
        # Setup mocks
        mock_verify_api_key.return_value = mock_api_key
        mock_get_db.return_value = mock_db
        mock_check_token_limit.return_value = (True, 1000)
        
        # Mock compression
        mock_compress.return_value = ("compressed", {"@": "test"}, 0.8)
        mock_format.return_value = "DICT:@=test|PROMPT:compressed"
        
        # Mock LLM response
        mock_llm_response = LLMResponse(
            text="This is a test response",
            input_tokens=10,
            output_tokens=5,
            model="gpt-4",
            finish_reason="stop"
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_openai_client.return_value = mock_client_instance
        
        # Make request
        response = client.post(
            "/api/v1/complete",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "llm_provider": "openai",
                "llm_api_key": "sk-test-key",
                "compress": True,
                "compress_output": False,
            },
            headers={"X-API-Key": "test-api-key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "decompressed_response" in data
        assert data["decompressed_response"] == "This is a test response"
        assert "compression_stats" in data
        assert "llm_stats" in data
        assert data["llm_stats"]["provider"] == "openai"
        assert data["llm_stats"]["model"] == "gpt-4"
    
    @patch('api.routes.complete.verify_api_key')
    @patch('api.routes.complete.get_db')
    @patch('api.routes.complete.AnthropicClient')
    @patch('api.routes.complete.compress_prompt')
    @patch('api.routes.complete.format_for_llm')
    @patch('api.routes.complete.check_token_limit')
    @patch('api.routes.complete.increment_usage')
    def test_complete_with_anthropic(
        self,
        mock_increment_usage,
        mock_check_token_limit,
        mock_format,
        mock_compress,
        mock_anthropic_client,
        mock_get_db,
        mock_verify_api_key,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with Anthropic."""
        # Setup mocks
        mock_verify_api_key.return_value = mock_api_key
        mock_get_db.return_value = mock_db
        mock_check_token_limit.return_value = (True, 1000)
        
        # Mock compression
        mock_compress.return_value = ("compressed", {"@": "test"}, 0.8)
        mock_format.return_value = "DICT:@=test|PROMPT:compressed"
        
        # Mock LLM response
        mock_llm_response = LLMResponse(
            text="This is a Claude response",
            input_tokens=10,
            output_tokens=5,
            model="claude-3-opus-20240229",
            finish_reason="end_turn"
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_anthropic_client.return_value = mock_client_instance
        
        # Make request
        response = client.post(
            "/api/v1/complete",
            json={
                "prompt": "test prompt",
                "model": "claude-3-opus",
                "llm_provider": "anthropic",
                "llm_api_key": "sk-ant-test-key",
                "compress": True,
                "compress_output": False,
            },
            headers={"X-API-Key": "test-api-key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["decompressed_response"] == "This is a Claude response"
        assert data["llm_stats"]["provider"] == "anthropic"
    
    @patch('api.routes.complete.verify_api_key')
    @patch('api.routes.complete.get_db')
    @patch('api.routes.complete.OpenAIClient')
    def test_complete_with_invalid_llm_key(
        self,
        mock_openai_client,
        mock_get_db,
        mock_verify_api_key,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with invalid LLM API key."""
        # Setup mocks
        mock_verify_api_key.return_value = mock_api_key
        mock_get_db.return_value = mock_db
        
        # Mock LLM client to raise API key error
        mock_client_instance = Mock()
        mock_client_instance.complete.side_effect = LLMAPIKeyError("Invalid API key")
        mock_openai_client.return_value = mock_client_instance
        
        # Make request
        response = client.post(
            "/api/v1/complete",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "llm_provider": "openai",
                "llm_api_key": "invalid-key",
                "compress": False,
            },
            headers={"X-API-Key": "test-api-key"}
        )
        
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]
    
    @patch('api.routes.complete.verify_api_key')
    @patch('api.routes.complete.get_db')
    @patch('api.routes.complete.OpenAIClient')
    def test_complete_with_rate_limit(
        self,
        mock_openai_client,
        mock_get_db,
        mock_verify_api_key,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with rate limit error."""
        # Setup mocks
        mock_verify_api_key.return_value = mock_api_key
        mock_get_db.return_value = mock_db
        
        # Mock LLM client to raise rate limit error
        mock_client_instance = Mock()
        mock_client_instance.complete.side_effect = LLMRateLimitError("Rate limit exceeded")
        mock_openai_client.return_value = mock_client_instance
        
        # Make request
        response = client.post(
            "/api/v1/complete",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "llm_provider": "openai",
                "llm_api_key": "sk-test-key",
                "compress": False,
            },
            headers={"X-API-Key": "test-api-key"}
        )
        
        assert response.status_code == 429
    
    @patch('api.routes.complete.verify_api_key')
    @patch('api.routes.complete.get_db')
    @patch('api.routes.complete.OpenAIClient')
    @patch('api.routes.complete.compress_prompt')
    @patch('api.routes.complete.format_for_llm')
    @patch('api.routes.complete.decompress_llm_format')
    @patch('api.routes.complete.check_token_limit')
    @patch('api.routes.complete.increment_usage')
    def test_complete_with_output_compression(
        self,
        mock_increment_usage,
        mock_check_token_limit,
        mock_decompress,
        mock_format,
        mock_compress,
        mock_openai_client,
        mock_get_db,
        mock_verify_api_key,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint with output compression."""
        # Setup mocks
        mock_verify_api_key.return_value = mock_api_key
        mock_get_db.return_value = mock_db
        mock_check_token_limit.return_value = (True, 1000)
        
        # Mock compression
        mock_compress.return_value = ("compressed", {"@": "test"}, 0.8)
        mock_format.return_value = "DICT:@=test|PROMPT:compressed"
        
        # Mock LLM response (compressed format)
        mock_llm_response = LLMResponse(
            text="DICT:@=response|PROMPT:compressed text",
            input_tokens=10,
            output_tokens=5,
            model="gpt-4",
            finish_reason="stop"
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_openai_client.return_value = mock_client_instance
        
        # Mock decompression
        mock_decompress.return_value = "This is the decompressed response"
        
        # Make request
        response = client.post(
            "/api/v1/complete",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "llm_provider": "openai",
                "llm_api_key": "sk-test-key",
                "compress": True,
                "compress_output": True,
            },
            headers={"X-API-Key": "test-api-key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["decompressed_response"] == "This is the decompressed response"
        assert data["raw_llm_response"] == "DICT:@=response|PROMPT:compressed text"
        mock_decompress.assert_called_once()
    
    @patch('api.routes.complete.verify_api_key')
    @patch('api.routes.complete.get_db')
    @patch('api.routes.complete.OpenAIClient')
    def test_complete_without_compression(
        self,
        mock_openai_client,
        mock_get_db,
        mock_verify_api_key,
        client,
        mock_db,
        mock_api_key
    ):
        """Test complete endpoint without compression."""
        # Setup mocks
        mock_verify_api_key.return_value = mock_api_key
        mock_get_db.return_value = mock_db
        
        # Mock LLM response
        mock_llm_response = LLMResponse(
            text="Direct response",
            input_tokens=10,
            output_tokens=5,
            model="gpt-4",
            finish_reason="stop"
        )
        mock_client_instance = Mock()
        mock_client_instance.complete.return_value = mock_llm_response
        mock_openai_client.return_value = mock_client_instance
        
        # Make request
        response = client.post(
            "/api/v1/complete",
            json={
                "prompt": "test prompt",
                "model": "gpt-4",
                "llm_provider": "openai",
                "llm_api_key": "sk-test-key",
                "compress": False,
            },
            headers={"X-API-Key": "test-api-key"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["decompressed_response"] == "Direct response"
        assert data["compression_stats"]["compression_enabled"] is False

