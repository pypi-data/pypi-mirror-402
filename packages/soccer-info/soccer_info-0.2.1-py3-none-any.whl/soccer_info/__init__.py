"""Soccer Football Info API Python SDK.

A comprehensive Python SDK for accessing the Soccer Football Info API via RapidAPI.
Provides typed clients, request builders, and response models for soccer data.

Quick Start:
    >>> import soccer_info
    >>> client = soccer_info.quick_client()
    >>> championships = client.championships.get_list()

Advanced Usage:
    >>> from soccer_info.settings import SettingsBuilder
    >>> from soccer_info.client import HTTPXClient
    >>> 
    >>> client = HTTPXClient(
    ...     SettingsBuilder().with_api_key(environment="RAPIDAPI_KEY").build()
    ... )
    >>> championships = client.championships.get_list()

Modules:
    client: API client implementation with httpx
    settings: Configuration management with flexible authentication
    requests_: Request building components (headers, parameters, enums)
    responses: Pydantic models for parsing and validating API responses
"""
from . import client
from . import requests_
from . import responses
from . import settings

from typing import Optional

__version__ = "0.1.0"


def quick_client(
        setting: Optional[settings.Settings] = None,
) -> client.HTTPXClient:
    """Create a Soccer Football Info API client with sensible defaults.
    
    Convenience function that eliminates the need to manually construct 
    SettingsBuilder objects for basic usage scenarios.
    
    Args:
        setting: Custom settings instance. If None, creates default
            settings with API key from RAPIDAPI_KEY environment variable.
    
    Returns:
        HTTPXClient: Configured sync client ready for API calls.
    """
    return client.HTTPXClient(
        settings.SettingsBuilder().with_api_key().build() if setting is None else setting,
    )


def quick_async_client(
        setting: Optional[settings.Settings] = None,
) -> client.AsyncHTTPXClient:
    """Create an async_ Soccer Football Info API client with sensible defaults.
    
    Convenience function that eliminates the need to manually construct 
    SettingsBuilder objects for basic async_ usage scenarios.
    
    Args:
        setting: Custom settings instance. If None, creates default 
            settings with API key from RAPIDAPI_KEY environment variable.
    
    Returns:
        AsyncHTTPClient: Configured async_ client ready for API calls.
    """
    return client.AsyncHTTPXClient(
        settings.SettingsBuilder().with_api_key().build() if setting is None else setting,
    )
