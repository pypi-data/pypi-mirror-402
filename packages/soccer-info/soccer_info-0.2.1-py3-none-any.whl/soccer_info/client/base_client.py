from dataclasses import dataclass
from typing import Optional, TypeVar

from soccer_info.responses.base import ResponseComponent
from soccer_info.settings import Settings

T = TypeVar('T', bound=ResponseComponent)


@dataclass
class BaseClient:
    """Base client for Soccer Football Info API.
    
    Provides common configuration and settings shared by all client implementations.
    
    Attributes:
        settings: API configuration including authentication credentials
        default_language: Preferred language for API responses
    """
    settings: Settings
    default_language: Optional[str] = None
