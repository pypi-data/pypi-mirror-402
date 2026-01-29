"""
Tests for output compression feature.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from pcompresslr import Pcompresslr


def _mock_api_response(prompt: str):
    """Create a mock API response for testing."""
    # Simulate compression: replace repeated words with placeholders
    # Ensure compressed version is actually shorter
    compressed = prompt.replace("hello world", "@")
    # If no compression happened, simulate some compression
    if compressed == prompt:
        # For prompts without "hello world", simulate compression by shortening
        compressed = prompt[:len(prompt)//2] + "..."
        dictionary = {"...": prompt[len(prompt)//2:]}
    else:
        dictionary = {"@": "hello world"}
    
    llm_format = f"DICT:{';'.join(f'{k}={v}' for k, v in dictionary.items())};|PROMPT:{compressed}"
    
    # Calculate realistic sizes - compressed should be smaller
    original_size = len(prompt)
    compressed_size = len(compressed)
    # Ensure compression ratio is always < 1.0 (at least some compression)
    compression_ratio = min(0.8, compressed_size / original_size) if original_size > 0 else 0.8
    
    return {
        "compressed": compressed,
        "dictionary": dictionary,
        "llm_format": llm_format,
        "compression_ratio": compression_ratio,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "processing_time_ms": 10.5
    }


@patch('pcompresslr.core.PcompresslrAPIClient')
def test_basic_compression(mock_client_class):
    """Test basic compression without output compression."""
    # Mock the API client
    mock_client = MagicMock()
    mock_client.compress.return_value = _mock_api_response("hello world hello world hello world")
    mock_client_class.return_value = mock_client
    
    prompt = "hello world hello world hello world"
    compressor = Pcompresslr(prompt, model="gpt-4", compress_output=False, api_key="test-key")
    
    compressed = compressor.get_compressed_prompt()
    assert compressed is not None
    assert len(compressed) > 0
    
    stats = compressor.get_compression_stats()
    assert stats["original_size_chars"] == len(prompt)
    assert stats["compression_ratio"] <= 1.0
    assert stats["output_compression_enabled"] is False


@patch('pcompresslr.core.PcompresslrAPIClient')
def test_output_compression_enabled(mock_client_class):
    """Test that output compression adds instructions to prompt."""
    # Mock the API client
    mock_client = MagicMock()
    mock_client.compress.return_value = _mock_api_response("hello world hello world hello world")
    mock_client_class.return_value = mock_client
    
    prompt = "hello world hello world hello world"
    compressor = Pcompresslr(prompt, model="gpt-4", compress_output=True, api_key="test-key")
    
    compressed = compressor.get_compressed_prompt()
    assert compressed is not None
    assert "[Output in compressed format" in compressed or "DICT:" in compressed
    
    stats = compressor.get_compression_stats()
    assert stats["output_compression_enabled"] is True
    assert stats["instruction_tokens"] > 0
    assert stats["instruction_chars"] > 0


@patch('pcompresslr.core.PcompresslrAPIClient')
def test_input_size_increase(mock_client_class):
    """Test that output compression increases input size."""
    # Mock the API client
    mock_client = MagicMock()
    mock_client.compress.return_value = _mock_api_response("hello world hello world hello world")
    mock_client_class.return_value = mock_client
    
    prompt = "hello world hello world hello world"
    
    compressor_no_output = Pcompresslr(prompt, model="gpt-4", compress_output=False, api_key="test-key")
    compressor_with_output = Pcompresslr(prompt, model="gpt-4", compress_output=True, api_key="test-key")
    
    prompt_no_output = compressor_no_output.get_compressed_prompt()
    prompt_with_output = compressor_with_output.get_compressed_prompt()
    
    # Prompt with output compression should be longer
    assert len(prompt_with_output) > len(prompt_no_output)
    
    # Check the size increase
    instruction_tokens, instruction_chars = compressor_with_output.get_input_size_increase()
    assert instruction_tokens > 0
    assert instruction_chars > 0


@patch('pcompresslr.core.PcompresslrAPIClient')
def test_decompress_output(mock_client_class):
    """Test decompressing model output."""
    # Mock the API client
    mock_client = MagicMock()
    mock_client.compress.return_value = _mock_api_response("hello world hello world hello world")
    # Mock decompress to return the decompressed text
    mock_client.decompress.return_value = {"decompressed": "hello world hello world hello world"}
    mock_client_class.return_value = mock_client
    
    prompt = "hello world hello world hello world"
    compressor = Pcompresslr(prompt, model="gpt-4", compress_output=True, api_key="test-key")
    
    # Simulate a compressed model response
    # Format: DICT:key1=value1;key2=value2|PROMPT:compressed_text
    compressed_response = "DICT:@=hello world;|PROMPT:@ @ @"
    
    decompressed = compressor.decompress_output(compressed_response)
    assert decompressed is not None
    assert len(decompressed) > 0
    assert decompressed == "hello world hello world hello world"


@patch('pcompresslr.core.PcompresslrAPIClient')
def test_decompress_output_without_flag(mock_client_class):
    """Test that decompress_output fails if compress_output was False."""
    # Mock the API client
    mock_client = MagicMock()
    mock_client.compress.return_value = _mock_api_response("hello world hello world hello world")
    mock_client_class.return_value = mock_client
    
    prompt = "hello world hello world hello world"
    compressor = Pcompresslr(prompt, model="gpt-4", compress_output=False, api_key="test-key")
    
    with pytest.raises(ValueError, match="compress_output was False"):
        compressor.decompress_output("DICT:@=hello|PROMPT:@ @")


@patch('pcompresslr.core.PcompresslrAPIClient')
def test_compression_stats(mock_client_class):
    """Test that compression stats are accurate."""
    # Mock the API client
    mock_client = MagicMock()
    mock_client.compress.return_value = _mock_api_response("hello world hello world hello world")
    mock_client_class.return_value = mock_client
    
    prompt = "hello world hello world hello world"
    compressor = Pcompresslr(prompt, model="gpt-4", compress_output=True, api_key="test-key")
    
    stats = compressor.get_compression_stats()
    
    assert "original_size_chars" in stats
    assert "compressed_size_chars" in stats
    assert "original_tokens" in stats
    assert "compressed_tokens" in stats
    assert "compression_ratio" in stats
    assert "token_savings" in stats
    assert "token_savings_percent" in stats
    assert "output_compression_enabled" in stats
    assert "instruction_tokens" in stats
    assert "instruction_chars" in stats
    
    # Verify some basic relationships
    # Note: When output_compression_enabled=True, compressed_tokens may be > original_tokens
    # because instructions are added. But the base compression ratio should still be <= 1.0
    assert stats["compression_ratio"] <= 1.0
    # The base compressed prompt (from API) should be smaller than original
    # But final prompt with instructions may be larger
    assert stats["instruction_chars"] > 0  # Instructions should add some characters


@patch('pcompresslr.core.PcompresslrAPIClient')
def test_optimal_algorithm(mock_client_class):
    """Test that optimal algorithm works with output compression."""
    # Mock the API client
    mock_client = MagicMock()
    mock_client.compress.return_value = _mock_api_response("hello world hello world hello world")
    mock_client_class.return_value = mock_client
    
    prompt = "hello world hello world hello world"
    compressor = Pcompresslr(
        prompt, 
        model="gpt-4", 
        compress_output=True,
        use_optimal=True,
        api_key="test-key"
    )
    
    compressed = compressor.get_compressed_prompt()
    assert compressed is not None
    
    stats = compressor.get_compression_stats()
    assert stats["compression_ratio"] <= 1.0


@patch('pcompresslr.core.PcompresslrAPIClient')
def test_real_world_example(mock_client_class):
    """Test with a more realistic prompt."""
    prompt = """
    Please write a detailed explanation of machine learning algorithms.
    Include information about supervised learning, unsupervised learning, and reinforcement learning.
    Explain how neural networks work and their applications in modern AI systems.
    """
    
    # Mock the API client
    mock_client = MagicMock()
    mock_client.compress.return_value = _mock_api_response(prompt)
    mock_client_class.return_value = mock_client
    
    compressor = Pcompresslr(prompt, model="gpt-4", compress_output=True, api_key="test-key")
    
    compressed = compressor.get_compressed_prompt()
    assert compressed is not None
    # With output compression enabled, the final prompt includes instructions
    # so it may be longer than the original, but compression_ratio should still be < 1.0
    assert compressor.get_compression_stats()["compression_ratio"] < 1.0
    
    # Check that instruction is present
    assert "[Output in compressed format" in compressed or "DICT:" in compressed or "[Output:" in compressed
    
    stats = compressor.get_compression_stats()
    assert stats["output_compression_enabled"] is True

