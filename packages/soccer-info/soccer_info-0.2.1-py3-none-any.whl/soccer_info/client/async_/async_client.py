from abc import ABC, abstractmethod
import asyncio
import time
from typing import Type, Optional

from soccer_info.requests_.parameters import BaseParameters
from soccer_info.requests_.headers import Header
from soccer_info.client.base_client import BaseClient, T
from soccer_info.settings import Settings


class AsyncClient(BaseClient, ABC):
    """Asynchronous client with request throttling, domain client aggregation, and async context manager support.
    
    Attributes:
        championships: Domain client for championship-related endpoints
        matches: Domain client for match-related endpoints
        countries: Domain client for country-related endpoints
    """

    def __init__(
        self,
        settings: Settings,
        default_language: Optional[str] = None,
    ):
        """Initialize the base async client with common configuration.
        
        Args:
            settings: API configuration including authentication credentials
            default_language: Preferred language for API responses
        """
        super().__init__(settings, default_language)
        
        # Initialize throttling mechanism
        self._throttle_lock = asyncio.Lock()
        self._last_request_time: Optional[float] = None
        
        # Import here to avoid circular dependency
        from soccer_info.client.async_.domain.championships import AsyncChampionships
        from soccer_info.client.async_.domain.matches import AsyncMatches
        from soccer_info.client.async_.domain.countries import AsyncCountries
        self.championships = AsyncChampionships(self)
        self.matches = AsyncMatches(self)
        self.countries = AsyncCountries(self)

    async def __aenter__(self) -> 'AsyncClient':
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and close client."""
        await self.close()

    @abstractmethod
    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        ...

    @abstractmethod
    async def do_request(
        self,
        endpoint: str,
        params: BaseParameters,
        headers: Header,
        response_model: Type[T],
    ) -> T:
        """Execute async HTTP request to API endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., "/championships/list/")
            params: Request parameters to include in the API call
            headers: HTTP headers including RapidAPI authentication
            response_model: Pydantic model class for response validation
            
        Returns:
            Validated response object of the specified model type
        """
        ...
