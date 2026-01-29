"""VAP SDK Exceptions"""

from typing import Optional, Any


class VapError(Exception):
    """Base exception for VAP SDK"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class VapAuthError(VapError):
    """Authentication failed - invalid or missing API key"""
    pass


class VapInsufficientFundsError(VapError):
    """Insufficient balance for the requested operation"""
    
    def __init__(
        self,
        message: str,
        required: Optional[float] = None,
        available: Optional[float] = None,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.required = required
        self.available = available


class VapPresetNotFoundError(VapError):
    """Requested preset does not exist"""
    pass


class VapExecutionError(VapError):
    """Media execution failed"""
    
    def __init__(
        self,
        message: str,
        execution_id: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.execution_id = execution_id
        self.stage = stage


class VapTimeoutError(VapError):
    """Operation timed out"""
    pass


class VapRateLimitError(VapError):
    """Rate limit exceeded"""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs: Any
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after