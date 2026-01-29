"""
Test demonstrating how users would call the pcompresslr Python package.

This test shows typical usage patterns that end users would follow when
using the pcompresslr library in their own code.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock


def test_basic_usage_example():
    """
    Example 1: Basic compression workflow
    
    This is the simplest way a user would use the package:
    1. Import the package
    2. Create a compressor with their prompt
    3. Get the compressed prompt
    4. Send it to their LLM
    """
    # Skip if API key is not available (for CI/CD environments)
    api_key = os.getenv("PCOMPRESLR_API_KEY")
    if not api_key:
        pytest.skip("PCOMPRESLR_API_KEY not set - skipping API-dependent test")
    
    from pcompresslr import Pcompresslr
    
    # User's original prompt
    prompt = "Write a detailed explanation of machine learning. " * 5
    
    # Step 1: Create compressor (compression happens automatically)
    compressor = Pcompresslr(
        prompt=prompt,
        model="gpt-4",
        compress_output=False,  # Just compress input
        use_optimal=False,      # Use fast greedy algorithm
        api_key=api_key
    )
    
    # Step 2: Get compressed prompt ready for LLM
    compressed_prompt = compressor.get_compressed_prompt()
    
    # Step 3: User would send compressed_prompt to their LLM
    # (In this test, we just verify it works)
    assert compressed_prompt is not None
    assert len(compressed_prompt) > 0
    assert "DICT:" in compressed_prompt or len(compressed_prompt) < len(prompt)
    
    # Step 4: Check compression stats
    stats = compressor.get_compression_stats()
    assert stats["compression_ratio"] <= 1.0
    assert stats["token_savings"] >= 0


def test_usage_with_output_compression():
    """
    Example 2: Using output compression to save tokens on model responses
    
    This shows how users can compress both input and output:
    1. Enable output compression
    2. Get prompt with compression instructions
    3. Send to LLM
    4. Decompress the model's response
    """
    api_key = os.getenv("PCOMPRESLR_API_KEY")
    if not api_key:
        pytest.skip("PCOMPRESLR_API_KEY not set - skipping API-dependent test")
    
    from pcompresslr import Pcompresslr
    
    prompt = "Explain quantum computing in detail. " * 4
    
    # Create compressor with output compression enabled
    compressor = Pcompresslr(
        prompt=prompt,
        model="gpt-4",
        compress_output=True,   # Enable output compression
        use_optimal=False,
        api_key=api_key
    )
    
    # Get prompt with compression instructions
    prompt_with_instructions = compressor.get_compressed_prompt()
    assert prompt_with_instructions is not None
    
    # Check that instructions were added
    stats = compressor.get_compression_stats()
    assert stats["output_compression_enabled"] is True
    assert stats["instruction_tokens"] > 0
    
    # Simulate: User sends prompt_with_instructions to LLM
    # and receives a compressed response
    # (In real usage, the LLM would return compressed output)
    mock_compressed_response = "DICT:@=quantum computing;|PROMPT:Explain @ in detail."
    
    # User decompresses the model's response
    decompressed_response = compressor.decompress_output(mock_compressed_response)
    assert decompressed_response is not None
    assert len(decompressed_response) > 0


def test_usage_with_optimal_algorithm():
    """
    Example 3: Using optimal algorithm for best compression
    
    Users who want the best possible compression can use the optimal algorithm.
    Note: This is slower but produces globally optimal results.
    """
    api_key = os.getenv("PCOMPRESLR_API_KEY")
    if not api_key:
        pytest.skip("PCOMPRESLR_API_KEY not set - skipping API-dependent test")
    
    from pcompresslr import Pcompresslr
    
    prompt = "machine learning " * 10 + "deep learning " * 10
    
    # Use optimal algorithm for best compression
    compressor = Pcompresslr(
        prompt=prompt,
        model="gpt-4",
        compress_output=False,
        use_optimal=True,  # Use optimal DP algorithm
        api_key=api_key
    )
    
    compressed = compressor.get_compressed_prompt()
    stats = compressor.get_compression_stats()
    
    assert compressed is not None
    assert stats["compression_ratio"] <= 1.0


def test_usage_with_environment_variable():
    """
    Example 4: Using environment variable for API key
    
    Users can set PCOMPRESLR_API_KEY environment variable instead of
    passing it explicitly.
    """
    api_key = os.getenv("PCOMPRESLR_API_KEY")
    if not api_key:
        pytest.skip("PCOMPRESLR_API_KEY not set - skipping API-dependent test")
    
    from pcompresslr import Pcompresslr
    
    # User sets API key via environment variable
    # (In this test, we'll use the existing env var)
    prompt = "hello world " * 5
    
    # API key is automatically read from environment
    compressor = Pcompresslr(
        prompt=prompt,
        model="gpt-4"
        # api_key not provided - will use PCOMPRESLR_API_KEY env var
    )
    
    compressed = compressor.get_compressed_prompt()
    assert compressed is not None


def test_usage_complete_workflow():
    """
    Example 5: Complete end-to-end workflow
    
    This demonstrates a realistic complete workflow that a user might follow:
    1. Prepare a long prompt with repetition
    2. Compress it
    3. Send to LLM
    4. If output compression enabled, decompress response
    5. Use the results
    """
    api_key = os.getenv("PCOMPRESLR_API_KEY")
    if not api_key:
        pytest.skip("PCOMPRESLR_API_KEY not set - skipping API-dependent test")
    
    from pcompresslr import Pcompresslr
    
    # User's original long prompt (e.g., system prompt with repetition)
    original_prompt = """
    You are a helpful AI assistant. Your task is to help users with their questions.
    You should be polite, accurate, and concise in your responses.
    Remember to always provide accurate information.
    You should be polite, accurate, and concise in your responses.
    Your task is to help users with their questions.
    """
    
    # Step 1: Compress the prompt
    compressor = Pcompresslr(
        prompt=original_prompt,
        model="gpt-4",
        compress_output=True,  # Also compress output
        use_optimal=False,     # Fast greedy algorithm
        api_key=api_key
    )
    
    # Step 2: Get compressed prompt
    compressed_prompt = compressor.get_compressed_prompt()
    
    # Step 3: Check how much we saved
    stats = compressor.get_compression_stats()
    print(f"\nOriginal tokens: {stats['original_tokens']}")
    print(f"Compressed tokens: {stats['compressed_tokens']}")
    print(f"Token savings: {stats['token_savings']} ({stats['token_savings_percent']:.1f}%)")
    print(f"Compression ratio: {stats['compression_ratio']:.2%}")
    
    # Step 4: User would send compressed_prompt to their LLM
    # For this test, we simulate a compressed response
    # In reality, the LLM would return something like:
    mock_llm_response = "DICT:@=help users with their questions;|PROMPT:I'll @."
    
    # Step 5: Decompress the LLM's response
    decompressed_response = compressor.decompress_output(mock_llm_response)
    
    # Verify everything worked
    assert compressed_prompt is not None
    assert stats["compression_ratio"] <= 1.0
    assert decompressed_response is not None


def test_usage_error_handling():
    """
    Example 6: Error handling
    
    Shows how users should handle errors when using the package.
    """
    from pcompresslr import Pcompresslr, APIKeyError, RateLimitError, APIRequestError
    
    # Test 1: Missing API key
    with pytest.raises(APIKeyError):
        # Temporarily remove API key
        old_key = os.environ.pop("PCOMPRESLR_API_KEY", None)
        try:
            compressor = Pcompresslr(
                prompt="test",
                model="gpt-4",
                api_key=None  # No API key provided
            )
        finally:
            # Restore API key if it existed
            if old_key:
                os.environ["PCOMPRESLR_API_KEY"] = old_key
    
    # Test 2: Invalid API key - this will try to connect to API, so skip if no API key available
    api_key = os.getenv("PCOMPRESLR_API_KEY")
    if not api_key:
        pytest.skip("PCOMPRESLR_API_KEY not set - skipping API connection test")
    
    # This test expects the API to reject an invalid key
    # In a real scenario, this would raise APIKeyError, but without mocking
    # it will fail with connection error if API is not available
    with pytest.raises((APIKeyError, APIRequestError)):
        compressor = Pcompresslr(
            prompt="test",
            model="gpt-4",
            api_key="invalid-key-12345"
        )


def test_usage_comparing_algorithms():
    """
    Example 7: Comparing greedy vs optimal algorithms
    
    Users might want to compare both algorithms to see which works better
    for their use case.
    """
    api_key = os.getenv("PCOMPRESLR_API_KEY")
    if not api_key:
        pytest.skip("PCOMPRESLR_API_KEY not set - skipping API-dependent test")
    
    from pcompresslr import Pcompresslr
    
    prompt = "artificial intelligence " * 8 + "machine learning " * 8
    
    # Try greedy algorithm
    compressor_greedy = Pcompresslr(
        prompt=prompt,
        model="gpt-4",
        use_optimal=False,
        api_key=api_key
    )
    stats_greedy = compressor_greedy.get_compression_stats()
    
    # Try optimal algorithm
    compressor_optimal = Pcompresslr(
        prompt=prompt,
        model="gpt-4",
        use_optimal=True,
        api_key=api_key
    )
    stats_optimal = compressor_optimal.get_compression_stats()
    
    # Compare results
    print(f"\nGreedy compression ratio: {stats_greedy['compression_ratio']:.2%}")
    print(f"Optimal compression ratio: {stats_optimal['compression_ratio']:.2%}")
    print(f"Greedy processing time: {stats_greedy.get('processing_time_ms', 'N/A')}ms")
    print(f"Optimal processing time: {stats_optimal.get('processing_time_ms', 'N/A')}ms")
    
    # Both should work
    assert stats_greedy["compression_ratio"] <= 1.0
    assert stats_optimal["compression_ratio"] <= 1.0


def test_usage_different_models():
    """
    Example 8: Using different LLM models
    
    Users can specify different models for accurate token counting.
    """
    api_key = os.getenv("PCOMPRESLR_API_KEY")
    if not api_key:
        pytest.skip("PCOMPRESLR_API_KEY not set - skipping API-dependent test")
    
    from pcompresslr import Pcompresslr
    
    prompt = "test prompt " * 5
    
    # Use GPT-4
    compressor_gpt4 = Pcompresslr(
        prompt=prompt,
        model="gpt-4",
        api_key=api_key
    )
    
    # Use GPT-3.5-turbo
    compressor_gpt35 = Pcompresslr(
        prompt=prompt,
        model="gpt-3.5-turbo",
        api_key=api_key
    )
    
    # Both should work
    assert compressor_gpt4.get_compressed_prompt() is not None
    assert compressor_gpt35.get_compressed_prompt() is not None
    
    # Token counts might differ slightly between models
    stats_gpt4 = compressor_gpt4.get_compression_stats()
    stats_gpt35 = compressor_gpt35.get_compression_stats()
    
    assert stats_gpt4["compression_ratio"] <= 1.0
    assert stats_gpt35["compression_ratio"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

