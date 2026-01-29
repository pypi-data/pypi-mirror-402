from abc import ABC, abstractmethod
from typing import Type, Optional

from soccer_info.requests_.parameters import BaseParameters
from soccer_info.requests_.headers import Header
from soccer_info.client.base_client import BaseClient, T
from soccer_info.settings import Settings


class Client(BaseClient, ABC):
    """Synchronous client with domain client aggregation and context manager support.
    
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
        """Initialize the base client with common configuration.
        
        Args:
            settings: API configuration including authentication credentials
            default_language: Preferred language for API responses
        """
        super().__init__(settings, default_language)
        
        # Import here to avoid circular dependency
        from soccer_info.client.sync.domain.championships import Championships
        from soccer_info.client.sync.domain.matches import Matches
        from soccer_info.client.sync.domain.countries import Countries
        self.championships = Championships(self)
        self.matches = Matches(self)
        self.countries = Countries(self)

    def __enter__(self) -> 'Client':
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and close client."""
        self.close()

    @abstractmethod
    def close(self) -> None:
        """Close the HTTP client and release resources."""
        ...

    @abstractmethod
    def do_request(
        self,
        endpoint: str,
        params: BaseParameters,
        headers: Header,
        response_model: Type[T],
    ) -> T:
        """Execute HTTP request to API endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., "/championships/list/")
            params: Request parameters to include in the API call
            headers: HTTP headers including RapidAPI authentication
            response_model: Pydantic model class for response validation
            
        Returns:
            Validated response object of the specified model type
        """
        ...
