import httpx
from typing import Optional, Type

from soccer_info.requests_.headers import Header
from soccer_info.requests_.parameters import BaseParameters
from soccer_info.responses.base import ResponseHeaders
from soccer_info.settings import Settings
from .client import Client, T


class HTTPXClient(Client):
    """httpx-based implementation with lazy initialization and automatic resource cleanup.
    
    Example:
        >>> from soccer_info import quick_client
        >>> client = quick_client()
        >>> championships = client.championships.get_list()
        >>> for champ in championships.result:
        ...     print(f'{champ.name} (ID: {champ.id})' )
    """

    def __init__(
        self,
        settings: Settings,
        default_language: Optional[str] = None,
    ):
        """Initialize the httpx-based client.
        
        Args:
            settings: API configuration including authentication credentials
            default_language: Preferred language for API responses
        """
        super().__init__(settings, default_language)
        self._http_client: Optional[httpx.Client] = None

    @property
    def http_client(self) -> httpx.Client:
        """Lazily initialize and return the httpx client.
        
        The client is created on first access and reused for subsequent requests.
        """
        if self._http_client is None:
            self._http_client = httpx.Client(
                base_url=self.settings.base_url,
                timeout=self.settings.request_timeout,
            )
        return self._http_client

    def close(self) -> None:
        """Close the httpx client and release resources."""
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def do_request(
        self,
        endpoint: str,
        params: BaseParameters,
        headers: Header,
        response_model: Type[T],
    ) -> T:
        """Raises:
            httpx.HTTPStatusError: If the request fails with non-2xx status
            RuntimeError: If the response indicates an API error
        """
        response = self.http_client.get(
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
