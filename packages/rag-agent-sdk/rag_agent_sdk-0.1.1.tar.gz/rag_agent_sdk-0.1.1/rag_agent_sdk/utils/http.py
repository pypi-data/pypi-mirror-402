"""
HTTP utilities for RAG Agent SDK.

This module provides HTTP client functionality with retry, timeout, and error handling.
"""

import asyncio
from typing import Any, Dict, Optional, Union, AsyncIterator
import aiohttp
from aiohttp import ClientTimeout, ClientSession, ClientResponse

from ..exceptions import (
    RagAgentError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    ConnectionError,
    TimeoutError,
)


class HttpClient:
    """Async HTTP client with built-in error handling and retry logic."""
    
    def __init__(
        self,
        base_url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_multiplier: float = 2.0,
    ):
        """Initialize HTTP client.
        
        Args:
            base_url: Base URL for all requests.
            headers: Default headers to include in all requests.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts.
            retry_delay: Initial delay between retries in seconds.
            retry_multiplier: Multiplier for exponential backoff.
        """
        self.base_url = base_url.rstrip("/")
        self.default_headers = headers or {}
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_multiplier = retry_multiplier
        self._session: Optional[ClientSession] = None
    
    async def _get_session(self) -> ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                timeout=self.timeout,
                headers=self.default_headers,
            )
        return self._session
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"
    
    async def _handle_response(self, response: ClientResponse) -> Dict[str, Any]:
        """Handle response and raise appropriate exceptions."""
        status = response.status
        
        try:
            data = await response.json()
        except Exception:
            data = {"message": await response.text()}
        
        if 200 <= status < 300:
            return data
        
        message = data.get("message") or data.get("detail") or str(data)
        
        if status == 400:
            raise ValidationError(message, response=data)
        elif status == 401:
            raise AuthenticationError(message, response=data)
        elif status == 403:
            raise AuthorizationError(message, response=data)
        elif status == 404:
            raise NotFoundError(message, response=data)
        elif status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                response=data,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif 500 <= status < 600:
            raise ServerError(message, status_code=status, response=data)
        else:
            raise RagAgentError(message, status_code=status, response=data)
    
    def _is_retryable(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        if isinstance(error, (ServerError, RateLimitError)):
            return True
        if isinstance(error, aiohttp.ClientError):
            return True
        return False
    
    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a request with retry logic."""
        session = await self._get_session()
        url = self._build_url(path)
        
        last_error: Optional[Exception] = None
        delay = self.retry_delay
        
        for attempt in range(self.max_retries + 1):
            try:
                async with session.request(method, url, **kwargs) as response:
                    return await self._handle_response(response)
            
            except (RateLimitError, ServerError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = delay
                    if isinstance(e, RateLimitError) and e.retry_after:
                        wait_time = e.retry_after
                    await asyncio.sleep(wait_time)
                    delay *= self.retry_multiplier
            
            except aiohttp.ClientConnectionError as e:
                last_error = ConnectionError(str(e), original_error=e)
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= self.retry_multiplier
            
            except asyncio.TimeoutError:
                last_error = TimeoutError(timeout=self.timeout.total)
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= self.retry_multiplier
            
            except (AuthenticationError, AuthorizationError, NotFoundError, ValidationError):
                raise
            
            except Exception as e:
                raise RagAgentError(str(e))
        
        if last_error:
            raise last_error
        raise RagAgentError("Request failed after retries")
    
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make GET request."""
        return await self._request_with_retry(
            "GET",
            path,
            params=params,
            headers=headers,
        )
    
    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        return await self._request_with_retry(
            "POST",
            path,
            json=json,
            data=data,
            params=params,
            headers=headers,
        )
    
    async def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make PUT request."""
        return await self._request_with_retry(
            "PUT",
            path,
            json=json,
            headers=headers,
        )
    
    async def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self._request_with_retry(
            "DELETE",
            path,
            params=params,
            headers=headers,
        )
    
    async def stream(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> AsyncIterator[str]:
        """Make streaming POST request."""
        session = await self._get_session()
        url = self._build_url(path)
        
        async with session.post(url, json=json, headers=headers) as response:
            if response.status != 200:
                await self._handle_response(response)
            
            async for line in response.content:
                if line:
                    decoded = line.decode("utf-8").strip()
                    if decoded:
                        yield decoded
    
    async def upload_file(
        self,
        path: str,
        file_data: bytes,
        filename: str,
        field_name: str = "file",
        extra_fields: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Upload a file using multipart form data."""
        session = await self._get_session()
        url = self._build_url(path)
        
        form = aiohttp.FormData()
        form.add_field(
            field_name,
            file_data,
            filename=filename,
            content_type="application/octet-stream",
        )
        
        if extra_fields:
            for key, value in extra_fields.items():
                form.add_field(key, value)
        
        async with session.post(url, data=form, headers=headers) as response:
            return await self._handle_response(response)
