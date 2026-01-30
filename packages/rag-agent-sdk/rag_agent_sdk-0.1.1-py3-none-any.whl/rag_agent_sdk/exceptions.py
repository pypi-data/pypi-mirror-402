"""
RAG Agent SDK Exceptions.

This module defines all exception classes used by the RAG Agent SDK.
"""

from typing import Any, Dict, Optional


class RagAgentError(Exception):
    """Base exception for RAG Agent SDK.
    
    All SDK-specific exceptions inherit from this class.
    
    Attributes:
        message: Error message describing what went wrong.
        status_code: HTTP status code if applicable.
        response: Raw response data from the server.
        error_code: Application-specific error code.
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        self.error_code = error_code
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"error_code={self.error_code!r})"
        )


class AuthenticationError(RagAgentError):
    """Authentication failed (401).
    
    Raised when the API key or token is invalid or missing.
    """
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        # Add helpful fix suggestions
        help_text = (
            f"{message}\n"
            "How to fix:\n"
            "  1. Set RAG_AGENT_API_KEY environment variable, or\n"
            "  2. Pass api_key='your-key' to the client constructor, or\n"
            "  3. Use supabase_service_key for Supabase Auth"
        )
        super().__init__(help_text, status_code=401, **kwargs)


class AuthorizationError(RagAgentError):
    """Permission denied (HTTP 403).
    
    Raised when the authenticated user lacks permission for the requested action.
    """
    
    def __init__(
        self,
        message: str = "Permission denied",
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=403, response=response)


class NotFoundError(RagAgentError):
    """Resource not found (HTTP 404).
    
    Base class for specific not-found errors.
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        response: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(message, status_code=404, response=response)


class DatasetNotFoundError(NotFoundError):
    """Dataset not found.
    
    Raised when a requested dataset does not exist.
    """
    
    def __init__(
        self,
        dataset_id: str,
        message: Optional[str] = None,
    ):
        msg = message or f"Dataset not found: {dataset_id}"
        super().__init__(
            message=msg,
            resource_type="dataset",
            resource_id=dataset_id,
        )
        self.dataset_id = dataset_id


class DocumentNotFoundError(NotFoundError):
    """Document not found.
    
    Raised when a requested document does not exist.
    """
    
    def __init__(
        self,
        doc_id: str,
        dataset_id: Optional[str] = None,
        message: Optional[str] = None,
    ):
        msg = message or f"Document not found: {doc_id}"
        super().__init__(
            message=msg,
            resource_type="document",
            resource_id=doc_id,
        )
        self.doc_id = doc_id
        self.dataset_id = dataset_id


class ValidationError(RagAgentError):
    """Request validation failed (HTTP 400).
    
    Raised when request parameters fail validation.
    """
    
    def __init__(
        self,
        message: str = "Validation error",
        response: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Any]] = None,
    ):
        self.errors = errors or {}
        super().__init__(message, status_code=400, response=response)


class RateLimitError(RagAgentError):
    """Rate limit exceeded (HTTP 429).
    
    Raised when too many requests are made in a short period.
    
    Attributes:
        retry_after: Seconds to wait before retrying.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        response: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code=429, response=response)


class ServerError(RagAgentError):
    """Server error (HTTP 5xx).
    
    Raised when the server encounters an internal error.
    """
    
    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = 500,
        response: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=status_code, response=response)


class ConnectionError(RagAgentError):
    """Connection error.
    
    Raised when unable to connect to the RAG Agent server.
    """
    
    def __init__(
        self,
        message: str = "Failed to connect to server",
        original_error: Optional[Exception] = None,
        base_url: Optional[str] = None,
    ):
        self.original_error = original_error
        self.base_url = base_url
        # Add helpful fix suggestions
        help_text = (
            f"{message}\n"
            "How to fix:\n"
            f"  1. Check if the server is running at {base_url or 'the configured URL'}\n"
            "  2. Verify RAG_AGENT_BASE_URL environment variable\n"
            "  3. Check network connectivity and firewall settings"
        )
        super().__init__(help_text)


class TimeoutError(RagAgentError):
    """Request timeout.
    
    Raised when a request exceeds the configured timeout.
    """
    
    def __init__(
        self,
        message: str = "Request timed out",
        timeout: Optional[float] = None,
    ):
        self.timeout = timeout
        super().__init__(message)
