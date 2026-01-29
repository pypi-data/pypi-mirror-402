from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from soccer_info.requests_ import Header
from soccer_info.responses import ChampionshipListResponse, ChampionshipViewResponse
from soccer_info.client.base_client import BaseClient


@dataclass
class Championships(ABC):
    """Domain client for championship-related API endpoints.

    Provides methods to retrieve championship information including
    lists, detailed views with seasons, groups, and standings.

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

    def _get_language(self, language: Optional[str]) -> str:
        """Get language code, falling back to client default."""
        return language or self.client.default_language

    @abstractmethod
    def get_list(
        self,
        page: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
    ) -> ChampionshipListResponse:
        """Retrieve a page from the list of all championships.

        This is a paginated endpoint. Use the page parameter to navigate
        through results.

        Args:
            page: Page number for pagination (default: 1)
            country: Country code to filter championships (e.g., "IT", "ES")
            language: Language code for response (default: en_US)

        Returns:
            ChampionshipListResponse containing list of championships with pagination
        """
        pass

    @abstractmethod
    def get_by_id(
        self,
        championship_id: str,
        language: Optional[str] = None,
    ) -> ChampionshipViewResponse:
        """Retrieve detailed championship data including seasons and standings.

        Returns championship details with all seasons, groups within seasons,
        and full standings tables.

        Args:
            championship_id: The unique identifier of the championship
            language: Language code for response (default: en_US)

        Returns:
            ChampionshipViewResponse containing detailed championship data
        """
        pass
