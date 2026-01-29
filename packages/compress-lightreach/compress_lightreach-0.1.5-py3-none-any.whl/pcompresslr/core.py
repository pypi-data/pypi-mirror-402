"""
Core Pcompresslr class for compressing prompts and optionally model outputs.
"""

from typing import Dict, Tuple, Optional

from .api_client import PcompresslrAPIClient, APIKeyError, RateLimitError, APIRequestError


class Pcompresslr:
    """
    Main interface for prompt compression with optional output compression.
    
    Usage:
        # Complete a prompt (compresses, calls LLM, decompresses)
        compressor = Pcompresslr(
            model="gpt-4",
            api_key="your-key",
            llm_provider="openai",
            llm_api_key="your-llm-key"
        )
        result = compressor.complete("Your prompt here")
        print(result["decompressed_response"])
    """
    
    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        compress_output: bool = False,
        use_optimal: bool = False,
        llm_provider: Optional[str] = None,
        llm_api_key: Optional[str] = None
    ):
        """
        Initialize the compressor.
        
        Args:
            model: LLM model name for tokenization (e.g., 'gpt-4', 'gpt-3.5-turbo')
            api_key: API key for authentication. If not provided, checks PCOMPRESLR_API_KEY env var.
            api_url: Base URL for the API. If not provided, uses PCOMPRESLR_API_URL env var or production URL.
            compress_output: If True, instruct the model to output in compressed format
            use_optimal: If True, use optimal DP algorithm, else use fast greedy
            llm_provider: LLM provider ('openai' or 'anthropic') - for caching LLM API key
            llm_api_key: LLM provider API key - cached for use with complete() method
        
        Note:
            When compress_output=True, the input prompt size will increase due to
            compression instructions. The benefit is that the model's output will
            also be compressed, potentially saving tokens on the response.
        
        Raises:
            APIKeyError: If API key is not provided and not found in environment
        """
        self.model = model
        self.compress_output = compress_output
        self.use_optimal = use_optimal
        
        # Cache LLM provider and API key for complete() method
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key
        
        # Initialize API client (uses production URL by default, can be overridden via api_url param or PCOMPRESLR_API_URL env var)
        self.api_client = PcompresslrAPIClient(api_key=api_key, api_url=api_url)
    
    def set_llm_key(self, provider: str, api_key: str):
        """
        Set LLM provider API key for use with complete() method.
        
        Args:
            provider: LLM provider ('openai' or 'anthropic')
            api_key: LLM provider API key
        """
        if provider not in ["openai", "anthropic"]:
            raise ValueError(f"Unsupported provider: {provider}. Must be 'openai' or 'anthropic'")
        self.llm_provider = provider
        self.llm_api_key = api_key
    
    def clear_llm_key(self):
        """Clear cached LLM provider API key."""
        self.llm_provider = None
        self.llm_api_key = None
    
    def has_llm_key(self) -> bool:
        """Check if LLM API key is set."""
        return self.llm_provider is not None and self.llm_api_key is not None
    
    def get_api_url(self) -> str:
        """Get the current API URL being used."""
        return self.api_client.api_url
    
    def complete(
        self,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
        llm_provider: Optional[str] = None,
        llm_api_key: Optional[str] = None,
        compress: bool = True,
        compress_output: bool = False,
        use_optimal: Optional[bool] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """
        Complete a prompt with compression, LLM call, and decompression in one request.
        
        This is the only public method for using the compression service. Clients never
        see compressed prompts or dictionaries - everything is handled internally.
        
        Args:
            prompt: The prompt to complete. Required parameter.
            model: LLM model name. If None, uses the model from constructor.
            llm_provider: LLM provider ('openai' or 'anthropic'). If None, uses cached provider or requires it.
            llm_api_key: LLM provider API key. If None, uses cached key or requires it.
            compress: Whether to compress the prompt (default: True)
            compress_output: Whether to request compressed output from LLM (default: False)
            use_optimal: Whether to use optimal algorithm. If None, uses constructor setting.
            temperature: LLM temperature setting (optional)
            max_tokens: Maximum tokens to generate (optional)
            tags: Optional dictionary of tags for cost attribution (e.g., {'team': 'marketing'})
        
        Returns:
            Dictionary containing:
                - decompressed_response: Final decompressed response
                - compression_stats: Input compression statistics
                - llm_stats: LLM usage statistics
                - warnings: Any warnings
        
        Raises:
            ValueError: If LLM provider/key not provided and not cached
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIRequestError: For other API errors
        """
        # Prompt is required for complete()
        if prompt is None:
            raise ValueError(
                "prompt is required for complete(). Provide it as a parameter."
            )
        prompt_to_use = prompt
        
        # Use model from parameter or constructor
        model_to_use = model if model is not None else self.model
        
        # Get LLM provider - from parameter, cached, or error
        provider_to_use = llm_provider or self.llm_provider
        if not provider_to_use:
            raise ValueError(
                "LLM provider is required. Provide it as a parameter or set it in constructor/set_llm_key()."
            )
        
        # Get LLM API key - from parameter, cached, or error
        key_to_use = llm_api_key or self.llm_api_key
        if not key_to_use:
            raise ValueError(
                "LLM API key is required. Provide it as a parameter or set it in constructor/set_llm_key()."
            )
        
        # Cache the provider and key if provided
        if llm_provider and llm_api_key:
            self.llm_provider = llm_provider
            self.llm_api_key = llm_api_key
        
        # Determine algorithm
        algorithm = "optimal" if (use_optimal if use_optimal is not None else self.use_optimal) else "greedy"
        
        # Make the complete request
        try:
            result = self.api_client.complete(
                prompt=prompt_to_use,
                model=model_to_use,
                llm_provider=provider_to_use,
                llm_api_key=key_to_use,
                compress=compress,
                compress_output=compress_output,
                algorithm=algorithm,
                temperature=temperature,
                max_tokens=max_tokens,
                tags=tags,
            )
        except APIKeyError as e:
            raise APIKeyError(
                f"{str(e)}\n\n"
                "To get an API key, visit https://compress.lightreach.io or "
                "set the PCOMPRESLR_API_KEY environment variable."
            ) from e
        except RateLimitError as e:
            raise RateLimitError(
                f"{str(e)}\n\n"
                "You've exceeded your rate limit. Please wait before making more requests, "
                "or upgrade your subscription plan."
            ) from e
        except APIRequestError as e:
            raise APIRequestError(
                f"{str(e)}\n\n"
                "If this problem persists, please check https://compress.lightreach.io/status "
                "or contact support."
            ) from e
        
        return result

