"""
Smartflow SDK Exceptions.

All exceptions that can be raised by the Smartflow SDK.
"""


class SmartflowError(Exception):
    """Base exception for all Smartflow SDK errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def __str__(self):
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ConnectionError(SmartflowError):
    """Failed to connect to Smartflow instance."""
    pass


class AuthenticationError(SmartflowError):
    """Authentication failed (invalid API key or token)."""
    pass


class RateLimitError(SmartflowError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ComplianceError(SmartflowError):
    """Content blocked by compliance policy."""
    
    def __init__(self, message: str, violations: list = None, risk_score: float = None, **kwargs):
        super().__init__(message, **kwargs)
        self.violations = violations or []
        self.risk_score = risk_score


class ProviderError(SmartflowError):
    """AI provider error (OpenAI, Anthropic, etc.)."""
    
    def __init__(self, message: str, provider: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.provider = provider


class TimeoutError(SmartflowError):
    """Request timed out."""
    pass


class ValidationError(SmartflowError):
    """Request validation failed."""
    pass


class CacheError(SmartflowError):
    """Cache operation failed."""
    pass


def raise_for_status(response_data: dict, status_code: int):
    """
    Raise appropriate exception based on response data and status code.
    
    Args:
        response_data: JSON response from API
        status_code: HTTP status code
    
    Raises:
        Appropriate SmartflowError subclass
    """
    if status_code < 400:
        return
    
    error = response_data.get("error", {})
    if isinstance(error, str):
        message = error
        code = None
    else:
        message = error.get("message", "Unknown error")
        code = error.get("code")
    
    details = response_data.get("details", {})
    
    if status_code == 401:
        raise AuthenticationError(message, code=code, details=details)
    
    if status_code == 429:
        retry_after = error.get("retry_after") if isinstance(error, dict) else None
        raise RateLimitError(message, retry_after=retry_after, code=code, details=details)
    
    if status_code == 403 and "compliance" in message.lower():
        violations = error.get("violations", []) if isinstance(error, dict) else []
        risk_score = error.get("risk_score") if isinstance(error, dict) else None
        raise ComplianceError(message, violations=violations, risk_score=risk_score, code=code)
    
    if status_code == 502 or status_code == 503:
        provider = error.get("provider") if isinstance(error, dict) else None
        raise ProviderError(message, provider=provider, code=code, details=details)
    
    if status_code == 504:
        raise TimeoutError(message, code=code, details=details)
    
    if status_code == 400:
        raise ValidationError(message, code=code, details=details)
    
    raise SmartflowError(message, code=code, details=details)

