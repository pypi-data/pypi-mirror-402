"""
RAG Agent SDK Configuration.

This module handles configuration from multiple sources:
- Constructor parameters (highest priority)
- Environment variables
- Configuration files (lowest priority)

Environment Variables:
    RAG_AGENT_BASE_URL: Base URL of the RAG Agent server
    RAG_AGENT_API_KEY: API key for authentication
    RAG_AGENT_TIMEOUT: Request timeout in seconds
    RAG_AGENT_MAX_RETRIES: Maximum retry attempts
    RAG_AGENT_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)
    RAG_AGENT_DEBUG: Enable debug mode (true/false)
"""

import os
from dataclasses import dataclass, field
from typing import Optional


# Environment variable names
ENV_BASE_URL = "RAG_AGENT_BASE_URL"
ENV_API_KEY = "RAG_AGENT_API_KEY"
ENV_JWT_TOKEN = "RAG_AGENT_JWT_TOKEN"
ENV_TIMEOUT = "RAG_AGENT_TIMEOUT"
ENV_MAX_RETRIES = "RAG_AGENT_MAX_RETRIES"
ENV_LOG_LEVEL = "RAG_AGENT_LOG_LEVEL"
ENV_DEBUG = "RAG_AGENT_DEBUG"

# Supabase environment variables
ENV_SUPABASE_URL = "RAG_AGENT_SUPABASE_URL"
ENV_SUPABASE_ANON_KEY = "RAG_AGENT_SUPABASE_ANON_KEY"
ENV_SUPABASE_SERVICE_KEY = "RAG_AGENT_SUPABASE_SERVICE_KEY"
ENV_SUPABASE_ACCESS_TOKEN = "RAG_AGENT_SUPABASE_ACCESS_TOKEN"

# Default values
DEFAULT_BASE_URL = "http://localhost:9621"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_LOG_LEVEL = "WARNING"


def get_env_bool(name: str, default: bool = False) -> bool:
    """Get boolean value from environment variable."""
    value = os.environ.get(name, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


def get_env_float(name: str, default: float) -> float:
    """Get float value from environment variable."""
    value = os.environ.get(name)
    if value:
        try:
            return float(value)
        except ValueError:
            pass
    return default


def get_env_int(name: str, default: int) -> int:
    """Get integer value from environment variable."""
    value = os.environ.get(name)
    if value:
        try:
            return int(value)
        except ValueError:
            pass
    return default


@dataclass
class SDKConfig:
    """SDK configuration with environment variable fallbacks.
    
    Priority: Constructor parameters > Environment variables > Defaults
    
    Example:
        ```python
        # Uses RAG_AGENT_BASE_URL and RAG_AGENT_API_KEY from environment
        config = SDKConfig.from_env()
        
        # Override specific values
        config = SDKConfig.from_env(base_url="http://custom:9621")
        ```
    """
    
    # Connection settings
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay: float = DEFAULT_RETRY_DELAY
    
    # Authentication
    api_key: Optional[str] = None
    jwt_token: Optional[str] = None
    api_key_header: str = "X-API-Key"
    
    # Supabase Auth
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    supabase_access_token: Optional[str] = None
    
    # Username/Password Auth
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Logging & Debug
    log_level: str = DEFAULT_LOG_LEVEL
    debug: bool = False
    
    # SDK metadata
    sdk_version: str = field(default="0.1.0", repr=False)
    user_agent: str = field(default="", repr=False)
    
    def __post_init__(self):
        """Set derived values after initialization."""
        if not self.user_agent:
            self.user_agent = f"rag-agent-sdk-python/{self.sdk_version}"
    
    @classmethod
    def from_env(
        cls,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        supabase_url: Optional[str] = None,
        supabase_anon_key: Optional[str] = None,
        supabase_service_key: Optional[str] = None,
        supabase_access_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        log_level: Optional[str] = None,
        debug: Optional[bool] = None,
        **kwargs,
    ) -> "SDKConfig":
        """Create configuration from environment variables with optional overrides.
        
        Args:
            base_url: Override RAG_AGENT_BASE_URL
            api_key: Override RAG_AGENT_API_KEY
            jwt_token: Override RAG_AGENT_JWT_TOKEN
            timeout: Override RAG_AGENT_TIMEOUT
            max_retries: Override RAG_AGENT_MAX_RETRIES
            supabase_url: Override RAG_AGENT_SUPABASE_URL
            supabase_anon_key: Override RAG_AGENT_SUPABASE_ANON_KEY (requires access_token)
            supabase_service_key: Override RAG_AGENT_SUPABASE_SERVICE_KEY (admin access)
            supabase_access_token: Override RAG_AGENT_SUPABASE_ACCESS_TOKEN
            username: Username for password auth
            password: Password for password auth
            log_level: Override RAG_AGENT_LOG_LEVEL
            debug: Override RAG_AGENT_DEBUG
            **kwargs: Additional configuration options
            
        Returns:
            SDKConfig instance with merged configuration.
        """
        return cls(
            base_url=base_url or os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL),
            api_key=api_key or os.environ.get(ENV_API_KEY),
            jwt_token=jwt_token or os.environ.get(ENV_JWT_TOKEN),
            timeout=timeout if timeout is not None else get_env_float(ENV_TIMEOUT, DEFAULT_TIMEOUT),
            max_retries=max_retries if max_retries is not None else get_env_int(ENV_MAX_RETRIES, DEFAULT_MAX_RETRIES),
            retry_delay=retry_delay if retry_delay is not None else DEFAULT_RETRY_DELAY,
            supabase_url=supabase_url or os.environ.get(ENV_SUPABASE_URL),
            supabase_anon_key=supabase_anon_key or os.environ.get(ENV_SUPABASE_ANON_KEY),
            supabase_service_key=supabase_service_key or os.environ.get(ENV_SUPABASE_SERVICE_KEY),
            supabase_access_token=supabase_access_token or os.environ.get(ENV_SUPABASE_ACCESS_TOKEN),
            username=username,
            password=password,
            log_level=log_level or os.environ.get(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL),
            debug=debug if debug is not None else get_env_bool(ENV_DEBUG, False),
            **kwargs,
        )
    
    def validate(self) -> None:
        """Validate configuration and raise helpful errors.
        
        Raises:
            ValueError: If configuration is invalid with helpful message.
        """
        if not self.base_url:
            raise ValueError(
                f"Missing base URL. Please set {ENV_BASE_URL} environment variable "
                f"or pass base_url parameter."
            )
        
        if not self.has_auth():
            import warnings
            warnings.warn(
                f"No authentication configured. Set {ENV_API_KEY} environment variable "
                f"or pass api_key parameter for authenticated requests.",
                UserWarning,
            )
    
    def has_auth(self) -> bool:
        """Check if any authentication is configured."""
        return any([
            self.api_key,
            self.jwt_token,
            self.supabase_service_key,
            self.supabase_anon_key and self.supabase_access_token,
            self.username and self.password,
        ])


def get_default_config() -> SDKConfig:
    """Get default SDK configuration from environment.
    
    This is a convenience function for quick setup.
    
    Example:
        ```python
        from rag_agent_sdk.config import get_default_config
        
        config = get_default_config()
        client = RagAgentClient(config=config)
        ```
    """
    return SDKConfig.from_env()
