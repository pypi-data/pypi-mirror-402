"""
Compress Light Reach - Intelligent compression algorithms for LLM prompts.
"""

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.1.0"

# Export main interface class
from .core import Pcompresslr

# Export API client and exceptions
from .api_client import (
    PcompresslrAPIClient,
    APIKeyError,
    RateLimitError,
    APIRequestError,
    PcompresslrAPIError,
)

__all__ = [
    "Pcompresslr",
    "PcompresslrAPIClient",
    "APIKeyError",
    "RateLimitError",
    "APIRequestError",
    "PcompresslrAPIError",
    "__version__",
]

