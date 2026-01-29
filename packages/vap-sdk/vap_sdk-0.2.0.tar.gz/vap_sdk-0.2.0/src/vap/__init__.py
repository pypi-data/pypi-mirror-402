"""
VAP SDK - Visual Audio Production
Give your Agent a Studio

Usage:
    from vap import VapClient
    
    client = VapClient(api_key="your-key")
    result = client.execute("streaming_campaign", text="Hello world")
"""

from vap.client import VapClient, AsyncVapClient
from vap.models import (
    VapResult,
    VapPreset,
    AccountInfo,
    PresetInfo,
)
from vap.exceptions import (
    VapError,
    VapAuthError,
    VapInsufficientFundsError,
    VapPresetNotFoundError,
    VapExecutionError,
    VapTimeoutError,
)

__version__ = "0.1.0"
__all__ = [
    # Clients
    "VapClient",
    "AsyncVapClient",
    # Models
    "VapResult",
    "VapPreset",
    "AccountInfo",
    "PresetInfo",
    # Exceptions
    "VapError",
    "VapAuthError",
    "VapInsufficientFundsError",
    "VapPresetNotFoundError",
    "VapExecutionError",
    "VapTimeoutError",
]