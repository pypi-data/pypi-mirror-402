"""
API client for PCompressLR cloud service.
"""

import os
import requests
from typing import Dict, Optional, Literal
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Try to find .env file in multiple locations:
    # 1. Backend directory (where this package is located)
    # 2. Current working directory
    # 3. backend/.env from project root
    
    # Get the directory where this file is located
    # Path(__file__) = backend/pcompresslr/api_client.py
    # .parent = backend/pcompresslr/
    # .parent = backend/
    current_file_dir = Path(__file__).parent.parent
    
    # Try loading from backend directory first
    env_paths = [
        current_file_dir / ".env",  # backend/.env
        Path.cwd() / ".env",  # Current working directory
        Path.cwd() / "backend" / ".env",  # backend/.env from project root
    ]
    
    # Try each path
    loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            loaded = True
            break
    
    # If no .env file found in specific locations, use default behavior (searches upward)
    if not loaded:
        load_dotenv()
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass
except Exception:
    # If anything goes wrong, just continue without .env loading
    pass


class PcompresslrAPIError(Exception):
    """Base exception for API errors."""
    pass


class APIKeyError(PcompresslrAPIError):
    """Exception raised when API key is invalid or missing."""
    pass


class RateLimitError(PcompresslrAPIError):
    """Exception raised when rate limit is exceeded."""
    pass


class APIRequestError(PcompresslrAPIError):
    """Exception raised for general API request errors."""
    pass


class PcompresslrAPIClient:
    """
    Client for interacting with PCompressLR cloud API.
    
    Usage:
        client = PcompresslrAPIClient(api_key="your-key")
        result = client.compress("your prompt", model="gpt-4")
    """
    
    DEFAULT_API_URL = "https://api.compress.lightreach.io"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: int = 120  # 2 minutes - complete() calls LLM which can take 30+ seconds
    ):
        """
        Initialize the API client.
        
        Args:
            api_key: API key for authentication. If not provided, will check
                    PCOMPRESLR_API_KEY environment variable.
            api_url: Base URL for the API. If not provided, uses default production URL.
                    Can also be set via PCOMPRESLR_API_URL environment variable.
                    This is primarily for internal/testing use - users should use the default.
            timeout: Request timeout in seconds (default: 10)
        
        Raises:
            APIKeyError: If API key is not provided and not found in environment
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("PCOMPRESLR_API_KEY")
        if not self.api_key:
            raise APIKeyError(
                "API key is required. Provide it as a parameter or set "
                "PCOMPRESLR_API_KEY environment variable."
            )
        
        # Basic validation - API keys should not be empty strings
        if not self.api_key.strip():
            raise APIKeyError(
                "API key cannot be empty. Please provide a valid API key."
            )
        
        # Get API URL from parameter or environment or use default
        self.api_url = (api_url or 
                       os.getenv("PCOMPRESLR_API_URL") or 
                       self.DEFAULT_API_URL).rstrip('/')
        
        self.timeout = timeout
        
        # Create session with retry strategy
        # Note: We don't retry on 401 (invalid API key) or 4xx errors - fail fast
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,  # Reduced from 3 for faster failure
            backoff_factor=0.3,  # Reduced backoff for faster retries
            status_forcelist=[429, 500, 502, 503, 504],  # Only retry on these status codes
            allowed_methods=["POST"],
            respect_retry_after_header=True
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "compress-lightreach-python/0.1.0"
        })
    
    def _make_request(
        self,
        endpoint: str,
        data: Dict,
        method: str = "POST"
    ) -> Dict:
        """
        Make an HTTP request to the API.
        
        Args:
            endpoint: API endpoint path (e.g., "/api/v1/compress")
            data: Request payload
            method: HTTP method (default: "POST")
        
        Returns:
            JSON response as dictionary
        
        Raises:
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIRequestError: For other API errors
        """
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout
            )
            
            # Handle different status codes
            if response.status_code == 401:
                try:
                    error_detail = response.json().get("detail", "Invalid API key")
                except:
                    error_detail = "Invalid API key"
                raise APIKeyError(
                    f"Authentication failed: {error_detail}. "
                    "Please check your API key at https://compress.lightreach.io"
                )
            
            elif response.status_code == 429:
                error_detail = response.json().get("detail", "Rate limit exceeded")
                raise RateLimitError(f"Rate limit exceeded: {error_detail}")
            
            elif response.status_code == 400:
                error_detail = response.json().get("detail", "Bad request")
                raise APIRequestError(f"Bad request: {error_detail}")
            
            elif response.status_code == 403:
                error_detail = response.json().get("detail", "Forbidden")
                raise APIRequestError(f"Forbidden: {error_detail}")
            
            elif not response.ok:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                raise APIRequestError(
                    f"API request failed (HTTP {response.status_code}): {error_detail}"
                )
            
            return response.json()
        
        except requests.exceptions.Timeout:
            raise APIRequestError(
                f"Request to {url} timed out after {self.timeout} seconds. "
                "The API may be experiencing high load or may be unreachable. "
                "Please check your internet connection and try again."
            )
        
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            # Check if this is a timeout-related connection error
            if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                raise APIRequestError(
                    f"Failed to connect to API at {self.api_url}. "
                    f"Error: {error_msg}. "
                    "Please check your internet connection and verify the API endpoint is accessible.\n\n"
                    f"If this problem persists, please check https://compress.lightreach.io/status or contact support."
                )
            raise APIRequestError(
                f"Failed to connect to API at {self.api_url}. "
                f"Error: {error_msg}. "
                "Please check your internet connection and verify the API endpoint is accessible.\n\n"
                f"If this problem persists, please check https://compress.lightreach.io/status or contact support."
            )
        
        except (APIKeyError, RateLimitError, APIRequestError):
            # Re-raise our custom exceptions
            raise
        
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"Request failed: {str(e)}")
    
    def compress(
        self,
        prompt: str,
        model: str = "gpt-4",
        algorithm: Literal["greedy", "optimal"] = "greedy",
        tags: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Compress a prompt using the cloud API.
        
        Args:
            prompt: The prompt text to compress
            model: LLM model name for tokenization (e.g., 'gpt-4', 'gpt-3.5-turbo')
            algorithm: Compression algorithm ('greedy' or 'optimal')
            tags: Optional dictionary of tags for cost attribution (e.g., {'team': 'marketing'})
        
        Returns:
            Dictionary containing:
                - compressed: Compressed prompt text
                - dictionary: Decompression dictionary
                - llm_format: LLM-ready formatted string
                - compression_ratio: Compression ratio
                - original_size: Original size in characters
                - compressed_size: Compressed size in characters
                - processing_time_ms: Processing time in milliseconds
                - algorithm: Algorithm used
        
        Raises:
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIRequestError: For other API errors
        """
        data = {
            "prompt": prompt,
            "model": model,
            "algorithm": algorithm
        }
        
        if tags is not None:
            data["tags"] = tags
        
        return self._make_request("/api/v1/compress", data)
    
    def decompress(self, llm_format: str) -> Dict:
        """
        Decompress an LLM-formatted compressed prompt.
        
        Args:
            llm_format: LLM-formatted compressed prompt string
        
        Returns:
            Dictionary containing:
                - decompressed: Decompressed original prompt
                - processing_time_ms: Processing time in milliseconds
        
        Raises:
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIRequestError: For other API errors
        """
        data = {
            "llm_format": llm_format
        }
        
        return self._make_request("/api/v1/decompress", data)
    
    def health_check(self) -> Dict:
        """
        Check API health status.
        
        Returns:
            Dictionary with health status information
        
        Raises:
            APIRequestError: If health check fails
        """
        try:
            response = self.session.get(
                f"{self.api_url}/health",
                timeout=5
            )
            if response.ok:
                return response.json()
            else:
                raise APIRequestError(f"Health check failed: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            raise APIRequestError(f"Health check failed: {str(e)}")
    
    def complete(
        self,
        prompt: str,
        model: str,
        llm_provider: Literal["openai", "anthropic"],
        llm_api_key: str,
        compress: bool = True,
        compress_output: bool = False,
        algorithm: Literal["greedy", "optimal"] = "greedy",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """
        Complete a prompt with compression, LLM call, and decompression in one request.
        
        Args:
            prompt: The prompt to complete
            model: LLM model name (e.g., 'gpt-4', 'claude-3-opus')
            llm_provider: LLM provider ('openai' or 'anthropic')
            llm_api_key: LLM provider API key
            compress: Whether to compress the prompt (default: True)
            compress_output: Whether to request compressed output from LLM (default: False)
            algorithm: Compression algorithm ('greedy' or 'optimal')
            temperature: LLM temperature setting (optional)
            max_tokens: Maximum tokens to generate (optional)
            tags: Optional dictionary of tags for cost attribution (e.g., {'team': 'marketing'})
        
        Returns:
            Dictionary containing:
                - decompressed_response: Final decompressed response
                - compressed_prompt: Compressed prompt sent to LLM (if compression enabled)
                - raw_llm_response: Raw LLM response before decompression (if output compression enabled)
                - compression_stats: Input compression statistics
                - llm_stats: LLM usage statistics
                - warnings: Any warnings
        
        Raises:
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
            APIRequestError: For other API errors
        """
        data = {
            "prompt": prompt,
            "model": model,
            "llm_provider": llm_provider,
            "llm_api_key": llm_api_key,
            "compress": compress,
            "compress_output": compress_output,
            "algorithm": algorithm,
        }
        
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens
        if tags is not None:
            data["tags"] = tags
        
        return self._make_request("/api/v1/complete", data)

