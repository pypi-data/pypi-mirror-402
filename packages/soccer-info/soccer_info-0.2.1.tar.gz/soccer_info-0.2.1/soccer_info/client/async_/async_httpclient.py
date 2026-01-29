import asyncio
import httpx
import time
from typing import Optional, Type

from soccer_info.requests_.headers import Header
from soccer_info.requests_.parameters import BaseParameters
from soccer_info.responses.base import ResponseHeaders
from soccer_info.settings import Settings
from soccer_info.client.async_.async_client import AsyncClient, T


class AsyncHTTPXClient(AsyncClient):
    """httpx-based implementation with lazy initialization and automatic resource cleanup.

    Example:
        >>> from soccer_info import quick_async_client
        >>> import asyncio
        >>> async def f():
        ...     async with quick_async_client() as client:
        ...         championships = await client.championships.get_list()
        ...         for champ in championships.result:
        ...             print(f'{champ.name} (ID: {champ.id})')
        >>> asyncio.run(f())
    """

    def __init__(
        self,
        settings: Settings,
        default_language: Optional[str] = None,
    ):
        """Initialize the httpx-based async client.
        
        Args:
            settings: API configuration including authentication credentials
            default_language: Preferred language for API responses
        """
        super().__init__(settings, default_language)
        self._async_http_client: Optional[httpx.AsyncClient] = None

    @property
    def async_http_client(self) -> httpx.AsyncClient:
        """Lazily initialize and return the httpx async client.
        
        The client is created on first access and reused for subsequent requests.
        """
        if self._async_http_client is None:
            self._async_http_client = httpx.AsyncClient(
                base_url=self.settings.base_url,
                timeout=self.settings.request_timeout,
            )
        return self._async_http_client

    async def close(self) -> None:
        """Close the httpx async client and release resources."""
        if self._async_http_client is not None:
            await self._async_http_client.aclose()
            self._async_http_client = None

    async def do_request(
        self,
        endpoint: str,
        params: BaseParameters,
        headers: Header,
        response_model: Type[T],
    ) -> T:
        """Implements request throttling to ensure minimum time between requests.
        
        Requests are throttled according to settings.request_throttle_seconds. 
        If requests come in faster than the throttle limit, they will be queued 
        and processed sequentially with the appropriate delay.
        
        Raises:
            httpx.HTTPStatusError: If the request fails with non-2xx status
            RuntimeError: If the response indicates an API error
        """
        # Acquire lock to ensure proper spacing between request sends
        async with self._throttle_lock:
            # Calculate time to wait based on throttle setting
            if self._last_request_time is not None:
                elapsed = time.time() - self._last_request_time
                wait_time = self.settings.request_throttle_seconds - elapsed
                
                if wait_time > 0:
                    # Wait to respect the throttle limit
                    await asyncio.sleep(wait_time)
            
            # Update last request time before sending
            self._last_request_time = time.time()
        
        # Execute the HTTP request outside the lock so responses can overlap
        response = await self.async_http_client.get(
            endpoint,
            params=params.to_dict(),
            headers=headers.to_dict(),
        )

        response.raise_for_status()

        # Parse JSON response
        parsed = response_model.model_validate_json(response.text)

        # Parse and attach response headers (Pydantic handles normalization and type conversion)
        parsed.response_headers = ResponseHeaders.model_validate(dict(response.headers))

        return parsed
