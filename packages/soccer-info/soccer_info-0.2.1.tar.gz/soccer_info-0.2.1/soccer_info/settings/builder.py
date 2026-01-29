import os
from typing import Optional, Callable
from .settings import Settings

DEFAULT_API_KEY_ENV = "RAPIDAPI_SOCCER_INFO_KEY"


class SettingsBuilder:
    """Fluent builder for Soccer Football Info API configuration.
    
    Provides flexible API key configuration from multiple sources including
    direct values, environment variables, and custom providers.
    """

    def __init__(self):
        """Initialize empty settings builder."""
        self._api_key: Optional[str] = None
        self._api_key_provider: Optional[Callable[[], str]] = None
        self._api_host: str = "soccer-football-info.p.rapidapi.com"
        self._base_url: str = "https://soccer-football-info.p.rapidapi.com"

    def with_api_key(
            self,
            key: Optional[str] = None,
            environment: Optional[str] = None,
            key_provider: Optional[Callable[[], str]] = None,
    ) -> 'SettingsBuilder':
        """Set the API key using one of multiple methods.
        
        By default, if no args passed, key will be loaded from environment 
        variable RAPIDAPI_KEY.
        
        Args:
            key: Direct API key value
            environment: Name of environment variable to load the key from
            key_provider: Callable function that returns an API key

        Returns:
            Self for method chaining
        """
        if key is not None:
            self._api_key = key
        elif environment:
            self._api_key = os.environ.get(environment)
        elif key_provider is not None:
            self._api_key_provider = key_provider
        else:
            if default_key := os.environ.get(DEFAULT_API_KEY_ENV):
                self._api_key = default_key
            else:
                raise ValueError(
                    f'At least one method for retrieving API key must be provided, '
                    f'or default environment variable ({DEFAULT_API_KEY_ENV}) populated.'
                )
        return self

    def with_host(self, host: str) -> 'SettingsBuilder':
        """Set custom API host (for testing or alternative endpoints).
        
        Args:
            host: The API host name
            
        Returns:
            Self for method chaining
        """
        self._api_host = host
        return self

    def with_base_url(self, base_url: str) -> 'SettingsBuilder':
        """Set custom base URL (for testing or alternative endpoints).
        
        Args:
            base_url: The base URL for API requests
            
        Returns:
            Self for method chaining
        """
        self._base_url = base_url
        return self

    def build(self) -> Settings:
        """Build and return a Settings instance with configured values."""
        api_key = self._api_key

        if api_key is None and self._api_key_provider is not None:
            api_key = self._api_key_provider()

        if api_key is None:
            raise ValueError("API key must be provided")

        return Settings(
            api_key=api_key,
            api_host=self._api_host,
            base_url=self._base_url
        )
