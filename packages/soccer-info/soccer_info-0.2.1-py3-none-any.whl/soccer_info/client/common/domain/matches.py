from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from soccer_info.requests_ import Header
from soccer_info.responses import (
    MatchViewBasicResponse,
    MatchViewFullResponse,
    MatchOddsResponse,
    MatchProgressiveResponse,
    MatchDayBasicResponse,
    MatchDayFullResponse,
    MatchByBasicResponse,
    MatchByFullResponse,
)
from soccer_info.client.base_client import BaseClient


@dataclass
class Matches(ABC):
    """Domain client for match-related API endpoints.

    Provides methods to retrieve match information including
    basic/full views, odds, progressive data, and filtered lists.

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

    # =========================================================================
    # Single Match Endpoints
    # =========================================================================

    @abstractmethod
    def get_view_basic(
        self,
        match_id: str,
        language: Optional[str] = None,
    ) -> MatchViewBasicResponse:
        """Retrieve basic match data.

        Returns match data including id, date, status, timer,
        championship data, match stats and match events.

        Args:
            match_id: The unique identifier of the match
            language: Language code for response

        Returns:
            MatchViewBasicResponse containing basic match data
        """
        pass

    @abstractmethod
    def get_view_full(
        self,
        match_id: str,
        language: Optional[str] = None,
    ) -> MatchViewFullResponse:
        """Retrieve full match data including odds.

        Returns match data including id, date, status, timer,
        championship data, match stats, match events and odds.

        Args:
            match_id: The unique identifier of the match
            language: Language code for response

        Returns:
            MatchViewFullResponse containing full match data with odds
        """
        pass

    @abstractmethod
    def get_odds(
        self,
        match_id: str,
    ) -> MatchOddsResponse:
        """Retrieve all match odds.

        Returns all available odds: 1x2, over/under, asian handicap,
        asian corner, first half variants. Odds from bet365 and unibet.

        Args:
            match_id: The unique identifier of the match

        Returns:
            MatchOddsResponse containing all match odds
        """
        pass

    @abstractmethod
    def get_progressive(
        self,
        match_id: str,
        language: Optional[str] = None,
        format: Optional[str] = None,
    ) -> MatchProgressiveResponse:
        """Retrieve progressive match data.

        Returns match stats and odds captured every 30 seconds.
        Data available since 2020-01-01. Live matches require ULTRA plan.

        Args:
            match_id: The unique identifier of the match
            language: Language code for response
            format: Response format ('json' or 'csv')

        Returns:
            MatchProgressiveResponse containing progressive match data
        """
        pass

    # =========================================================================
    # Day-Based Endpoints
    # =========================================================================

    @abstractmethod
    def get_by_day_basic(
        self,
        date: str,
        page: Optional[int] = None,
        language: Optional[str] = None,
        format: Optional[str] = None,
    ) -> MatchDayBasicResponse:
        """Retrieve all matches for a specific day with basic data.

        Paginated for today and future dates. Past dates return all results.

        Args:
            date: Date in YYYYMMDD format
            page: Page number for pagination
            language: Language code for response
            format: Response format ('json' or 'csv')

        Returns:
            MatchDayBasicResponse containing matches for the day
        """
        pass

    @abstractmethod
    def get_by_day_full(
        self,
        date: str,
        page: Optional[int] = None,
        language: Optional[str] = None,
        format: Optional[str] = None,
    ) -> MatchDayFullResponse:
        """Retrieve all matches for a specific day with full data.

        Includes odds data. Paginated for today and future dates.

        Args:
            date: Date in YYYYMMDD format
            page: Page number for pagination
            language: Language code for response
            format: Response format ('json' or 'csv')

        Returns:
            MatchDayFullResponse containing matches for the day with odds
        """
        pass

    # =========================================================================
    # Filter-Based Endpoints
    # =========================================================================

    @abstractmethod
    def get_by_filter_basic(
        self,
        championship_id: Optional[str] = None,
        manager_id: Optional[str] = None,
        stadium_id: Optional[str] = None,
        page: Optional[int] = None,
        language: Optional[str] = None,
    ) -> MatchByBasicResponse:
        """Retrieve matches filtered by championship, manager, or stadium.

        At least one filter should be provided. Multiple filters use AND logic.

        Args:
            championship_id: Championship ID to filter by
            manager_id: Manager ID to filter by
            stadium_id: Stadium ID to filter by
            page: Page number for pagination
            language: Language code for response

        Returns:
            MatchByBasicResponse containing filtered matches
        """
        pass

    @abstractmethod
    def get_by_filter_full(
        self,
        championship_id: Optional[str] = None,
        manager_id: Optional[str] = None,
        stadium_id: Optional[str] = None,
        page: Optional[int] = None,
        language: Optional[str] = None,
    ) -> MatchByFullResponse:
        """Retrieve matches filtered by championship, manager, or stadium with full data.

        Includes odds data. At least one filter should be provided.
        Multiple filters use AND logic.

        Args:
            championship_id: Championship ID to filter by
            manager_id: Manager ID to filter by
            stadium_id: Stadium ID to filter by
            page: Page number for pagination
            language: Language code for response

        Returns:
            MatchByFullResponse containing filtered matches with odds
        """
        pass
