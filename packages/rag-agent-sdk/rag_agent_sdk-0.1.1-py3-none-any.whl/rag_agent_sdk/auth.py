"""
RAG Agent SDK Authentication.

This module provides authentication handling for various auth methods.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import asyncio


@dataclass
class AuthConfig:
    """Authentication configuration.
    
    Supports multiple authentication methods:
    
    1. **LightRAG API Key**: Static key for admin access
       - Header: X-API-Key: <key>
       
    2. **Supabase Service Key**: Admin access via service key
       - Header: apikey: <service_key>
       
    3. **Supabase Anon Key + JWT**: User-level access
       - Headers: apikey: <anon_key> + Authorization: Bearer <token>
       - Note: anon_key alone will get 401 error!
       
    4. **JWT Token (AUTH_ACCOUNTS)**: Token-based auth
       - Header: Authorization: Bearer <token>
       
    5. **Username/Password**: Credential-based login
    """
    
    # Method 1: LightRAG API Key (admin access)
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    
    # Method 2: JWT Token (pre-obtained, for AUTH_ACCOUNTS)
    jwt_token: Optional[str] = None
    
    # Method 3: Supabase Auth
    # - supabase_service_key: Admin access, no JWT needed
    # - supabase_anon_key + supabase_access_token: User-level access
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None      # Public key, requires JWT
    supabase_service_key: Optional[str] = None   # Private key, admin access
    supabase_access_token: Optional[str] = None  # JWT token from Supabase Auth
    
    # Method 4: Username/Password login
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Token management
    _access_token: Optional[str] = field(default=None, repr=False)
    _token_expires_at: Optional[datetime] = field(default=None, repr=False)
    _refresh_token: Optional[str] = field(default=None, repr=False)
    
    def has_credentials(self) -> bool:
        """Check if any authentication credentials are configured."""
        return any([
            self.api_key,
            self.jwt_token,
            self.supabase_service_key,
            self.supabase_anon_key and self.supabase_access_token,
            self.username and self.password,
        ])
    
    def get_auth_method(self) -> Optional[str]:
        """Get the active authentication method.
        
        Returns:
            - 'api_key': Using LightRAG API Key
            - 'supabase_service': Using Supabase service key (admin)
            - 'supabase_anon_jwt': Using Supabase anon key + JWT
            - 'jwt_token': Using AUTH_ACCOUNTS JWT
            - 'password': Using username/password login
        """
        if self.api_key:
            return "api_key"
        if self.supabase_service_key:
            return "supabase_service"
        if self.supabase_anon_key and self.supabase_access_token:
            return "supabase_anon_jwt"
        if self.jwt_token:
            return "jwt_token"
        if self.username and self.password:
            return "password"
        return None


class AuthHandler:
    """Handle authentication for RAG Agent API.
    
    This class manages authentication state and provides headers
    for authenticated requests.
    """
    
    def __init__(self, config: AuthConfig, http_client=None):
        """Initialize authentication handler.
        
        Args:
            config: Authentication configuration.
            http_client: HTTP client for login requests.
        """
        self.config = config
        self._http_client = http_client
        self._lock = asyncio.Lock()
    
    def set_http_client(self, http_client) -> None:
        """Set HTTP client for login requests."""
        self._http_client = http_client
    
    async def get_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests.
        
        Generates headers based on the configured authentication method:
        
        1. LightRAG API Key: X-API-Key header
        2. Supabase Service Key: apikey header (admin access)
        3. Supabase Anon Key + JWT: apikey + Authorization headers
        4. JWT Token: Authorization header only
        
        Returns:
            Dictionary of headers to include in requests.
        """
        headers = {}
        auth_method = self.config.get_auth_method()
        
        # Method 1: LightRAG API Key (admin access)
        if auth_method == "api_key":
            headers[self.config.api_key_header] = self.config.api_key
            return headers
        
        # Method 2: Supabase Service Key (admin access, no JWT needed)
        if auth_method == "supabase_service":
            headers["apikey"] = self.config.supabase_service_key
            return headers
        
        # Method 3: Supabase Anon Key + JWT (user-level access)
        if auth_method == "supabase_anon_jwt":
            headers["apikey"] = self.config.supabase_anon_key
            headers["Authorization"] = f"Bearer {self.config.supabase_access_token}"
            return headers
        
        # Method 4 & 5: JWT Token or Username/Password login
        token = await self._get_valid_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    async def _get_valid_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if needed."""
        # Use pre-configured JWT token
        if self.config.jwt_token:
            return self.config.jwt_token
        
        # Use Supabase access token
        if self.config.supabase_access_token:
            return self.config.supabase_access_token
        
        # Check cached token
        if self.config._access_token:
            if self._is_token_valid():
                return self.config._access_token
            # Token expired, try to refresh
            if self.config._refresh_token:
                await self._refresh_access_token()
                if self.config._access_token:
                    return self.config._access_token
        
        # Login with username/password
        if self.config.username and self.config.password:
            await self._login()
            return self.config._access_token
        
        return None
    
    def _is_token_valid(self) -> bool:
        """Check if the current token is still valid."""
        if not self.config._access_token:
            return False
        if not self.config._token_expires_at:
            return True  # No expiration info, assume valid
        # Add buffer of 5 minutes
        return datetime.utcnow() < self.config._token_expires_at - timedelta(minutes=5)
    
    async def _login(self) -> None:
        """Login with username and password."""
        if not self._http_client:
            return
        
        async with self._lock:
            # Double-check after acquiring lock
            if self._is_token_valid():
                return
            
            try:
                response = await self._http_client.post(
                    "/login",
                    data={
                        "username": self.config.username,
                        "password": self.config.password,
                    },
                )
                
                self.config._access_token = response.get("access_token")
                
                # Calculate expiration time
                expires_in = response.get("expires_in", 3600)  # Default 1 hour
                self.config._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                self.config._refresh_token = response.get("refresh_token")
                
            except Exception:
                # Login failed, clear any existing tokens
                self.config._access_token = None
                self.config._token_expires_at = None
                raise
    
    async def _refresh_access_token(self) -> None:
        """Refresh the access token using refresh token."""
        if not self._http_client or not self.config._refresh_token:
            return
        
        async with self._lock:
            try:
                response = await self._http_client.post(
                    "/auth/refresh",
                    json={"refresh_token": self.config._refresh_token},
                )
                
                self.config._access_token = response.get("access_token")
                
                expires_in = response.get("expires_in", 3600)
                self.config._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                # Some servers return a new refresh token
                if "refresh_token" in response:
                    self.config._refresh_token = response["refresh_token"]
                    
            except Exception:
                # Refresh failed, need to re-login
                self.config._access_token = None
                self.config._token_expires_at = None
                self.config._refresh_token = None
    
    async def logout(self) -> None:
        """Clear authentication state."""
        self.config._access_token = None
        self.config._token_expires_at = None
        self.config._refresh_token = None
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return bool(
            self.config.api_key or
            self.config.jwt_token or
            self.config.supabase_access_token or
            self.config._access_token
        )
