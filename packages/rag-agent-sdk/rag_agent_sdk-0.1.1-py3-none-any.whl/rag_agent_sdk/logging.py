"""
RAG Agent SDK Logging.

This module provides logging and request tracing functionality.
"""

import logging
import uuid
from typing import Any, Dict, Optional
from functools import wraps
import time


# SDK-specific logger
logger = logging.getLogger("rag_agent_sdk")

# Request ID header name
REQUEST_ID_HEADER = "X-Request-ID"
SDK_VERSION_HEADER = "X-SDK-Version"
SDK_LANGUAGE_HEADER = "X-SDK-Language"


class SDKLogger:
    """Logger for SDK operations with request tracing.
    
    Features:
    - Automatic request ID generation
    - Request/response logging in debug mode
    - Performance timing
    - Structured logging
    
    Example:
        ```python
        from rag_agent_sdk.logging import SDKLogger, configure_logging
        
        # Enable debug logging
        configure_logging(level="DEBUG")
        
        # Create logger instance
        sdk_logger = SDKLogger(debug=True)
        ```
    """
    
    def __init__(
        self,
        debug: bool = False,
        log_level: str = "WARNING",
        sdk_version: str = "0.1.0",
    ):
        """Initialize SDK logger.
        
        Args:
            debug: Enable debug mode for verbose logging.
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
            sdk_version: SDK version for request headers.
        """
        self.debug = debug
        self.sdk_version = sdk_version
        self._configure_level(log_level)
    
    def _configure_level(self, level: str) -> None:
        """Configure logging level."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        log_level = level_map.get(level.upper(), logging.WARNING)
        
        if self.debug:
            log_level = logging.DEBUG
        
        logger.setLevel(log_level)
        
        # Add handler if none exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(log_level)
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    def generate_request_id(self) -> str:
        """Generate a unique request ID for tracing."""
        return f"sdk-{uuid.uuid4().hex[:16]}"
    
    def get_request_headers(self, request_id: Optional[str] = None) -> Dict[str, str]:
        """Get headers to include in API requests.
        
        Args:
            request_id: Optional custom request ID.
            
        Returns:
            Headers dict with request ID and SDK info.
        """
        return {
            REQUEST_ID_HEADER: request_id or self.generate_request_id(),
            SDK_VERSION_HEADER: self.sdk_version,
            SDK_LANGUAGE_HEADER: "python",
        }
    
    def log_request(
        self,
        method: str,
        url: str,
        request_id: str,
        body: Optional[Any] = None,
    ) -> None:
        """Log an outgoing request.
        
        Args:
            method: HTTP method.
            url: Request URL.
            request_id: Request ID for tracing.
            body: Request body (logged only in debug mode).
        """
        logger.debug(
            f"[{request_id}] -> {method} {url}"
        )
        if self.debug and body:
            logger.debug(f"[{request_id}] Request body: {self._truncate(body)}")
    
    def log_response(
        self,
        request_id: str,
        status_code: int,
        elapsed_ms: float,
        body: Optional[Any] = None,
    ) -> None:
        """Log an incoming response.
        
        Args:
            request_id: Request ID for tracing.
            status_code: HTTP status code.
            elapsed_ms: Request duration in milliseconds.
            body: Response body (logged only in debug mode).
        """
        level = logging.DEBUG if status_code < 400 else logging.WARNING
        logger.log(
            level,
            f"[{request_id}] <- {status_code} ({elapsed_ms:.0f}ms)"
        )
        if self.debug and body:
            logger.debug(f"[{request_id}] Response body: {self._truncate(body)}")
    
    def log_error(
        self,
        request_id: str,
        error: Exception,
        context: Optional[str] = None,
    ) -> None:
        """Log an error.
        
        Args:
            request_id: Request ID for tracing.
            error: The exception that occurred.
            context: Additional context about the error.
        """
        msg = f"[{request_id}] Error: {type(error).__name__}: {error}"
        if context:
            msg += f" ({context})"
        logger.error(msg)
    
    def log_retry(
        self,
        request_id: str,
        attempt: int,
        max_attempts: int,
        delay: float,
    ) -> None:
        """Log a retry attempt.
        
        Args:
            request_id: Request ID for tracing.
            attempt: Current attempt number.
            max_attempts: Maximum attempts.
            delay: Delay before retry in seconds.
        """
        logger.warning(
            f"[{request_id}] Retry {attempt}/{max_attempts} in {delay:.1f}s"
        )
    
    def _truncate(self, data: Any, max_length: int = 500) -> str:
        """Truncate data for logging."""
        s = str(data)
        if len(s) > max_length:
            return s[:max_length] + "... (truncated)"
        return s


def configure_logging(
    level: str = "WARNING",
    debug: bool = False,
    format_string: Optional[str] = None,
) -> None:
    """Configure SDK logging globally.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        debug: Enable debug mode.
        format_string: Custom format string for log messages.
        
    Example:
        ```python
        from rag_agent_sdk.logging import configure_logging
        
        # Enable debug logging
        configure_logging(level="DEBUG")
        
        # Or use debug mode
        configure_logging(debug=True)
        ```
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    log_level = logging.DEBUG if debug else level_map.get(level.upper(), logging.WARNING)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Configure logger
    logger.setLevel(log_level)
    
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    
    if format_string:
        formatter = logging.Formatter(format_string)
    else:
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class RequestTimer:
    """Context manager for timing requests."""
    
    def __init__(self):
        self.start_time: float = 0
        self.elapsed_ms: float = 0
    
    def __enter__(self) -> "RequestTimer":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
