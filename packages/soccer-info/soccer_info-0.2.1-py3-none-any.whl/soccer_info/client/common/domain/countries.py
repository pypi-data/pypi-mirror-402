from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from soccer_info.requests_ import Header
from soccer_info.responses import CountryListResponse
from soccer_info.client.base_client import BaseClient


@dataclass
class Countries(ABC):
    """Domain client for country-related API endpoints.

    Provides methods to retrieve country information.

    Attributes:
        client: Base client containing settings and do_request implementation
    """
    client: BaseClient

    def __post_init__(self):
        """Initialize the default header provider after dataclass initialization."""
        self._header_provider = lambda: Header(
            x_rapidapi_key=self.client.settings.api_key,
            x_rapidapi_host=self.client.settings.api_host,
        )

    @abstractmethod
    def get_list(
        self,
        format: Optional[str] = None,
    ) -> CountryListResponse:
        """Retrieve all countries with related item counts.

        Returns all countries with unique code and counts of related items
        (championships, managers, players, referees, stadiums, teams).

        Args:
            format: Response format ('json' or 'csv')

        Returns:
            CountryListResponse containing list of countries
        """
        pass
