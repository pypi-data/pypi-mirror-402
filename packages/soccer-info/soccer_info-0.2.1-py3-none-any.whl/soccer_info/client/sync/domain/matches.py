from dataclasses import dataclass
from typing import Optional

from soccer_info.requests_ import (
    MatchViewParameters,
    MatchOddsParameters,
    MatchProgressiveParameters,
    MatchDayParameters,
    MatchByParameters,
)
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
from ..client import Client
from ...common.domain.matches import Matches as CommonMatches


@dataclass
class Matches(CommonMatches):
    """Synchronous domain client for match-related API endpoints."""

    client: Client

    # =========================================================================
    # Single Match Endpoints
    # =========================================================================

    def get_view_basic(
        self,
        match_id: str,
        language: Optional[str] = None,
    ) -> MatchViewBasicResponse:
        return self.client.do_request(
            endpoint="/matches/view/basic/",
            params=MatchViewParameters(
                id=match_id,
                language=self._get_language(language),
            ),
            headers=self._header_provider(),
            response_model=MatchViewBasicResponse,
        )

    def get_view_full(
        self,
        match_id: str,
        language: Optional[str] = None,
    ) -> MatchViewFullResponse:
        return self.client.do_request(
            endpoint="/matches/view/full/",
            params=MatchViewParameters(
                id=match_id,
                language=self._get_language(language),
            ),
            headers=self._header_provider(),
            response_model=MatchViewFullResponse,
        )

    def get_odds(
        self,
        match_id: str,
    ) -> MatchOddsResponse:
        return self.client.do_request(
            endpoint="/matches/odds/",
            params=MatchOddsParameters(
                id=match_id,
            ),
            headers=self._header_provider(),
            response_model=MatchOddsResponse,
        )

    def get_progressive(
        self,
        match_id: str,
        language: Optional[str] = None,
        format: Optional[str] = None,
    ) -> MatchProgressiveResponse:
        return self.client.do_request(
            endpoint="/matches/view/progressive/",
            params=MatchProgressiveParameters(
                id=match_id,
                language=self._get_language(language),
                format=format,
            ),
            headers=self._header_provider(),
            response_model=MatchProgressiveResponse,
        )

    # =========================================================================
    # Day-Based Endpoints
    # =========================================================================

    def get_by_day_basic(
        self,
        date: str,
        page: Optional[int] = None,
        language: Optional[str] = None,
        format: Optional[str] = None,
    ) -> MatchDayBasicResponse:
        return self.client.do_request(
            endpoint="/matches/day/basic/",
            params=MatchDayParameters(
                date=date,
                page=page,
                language=self._get_language(language),
                format=format,
            ),
            headers=self._header_provider(),
            response_model=MatchDayBasicResponse,
        )

    def get_by_day_full(
        self,
        date: str,
        page: Optional[int] = None,
        language: Optional[str] = None,
        format: Optional[str] = None,
    ) -> MatchDayFullResponse:
        return self.client.do_request(
            endpoint="/matches/day/full/",
            params=MatchDayParameters(
                date=date,
                page=page,
                language=self._get_language(language),
                format=format,
            ),
            headers=self._header_provider(),
            response_model=MatchDayFullResponse,
        )

    # =========================================================================
    # Filter-Based Endpoints
    # =========================================================================

    def get_by_filter_basic(
        self,
        championship_id: Optional[str] = None,
        manager_id: Optional[str] = None,
        stadium_id: Optional[str] = None,
        page: Optional[int] = None,
        language: Optional[str] = None,
    ) -> MatchByBasicResponse:
        return self.client.do_request(
            endpoint="/matches/by/basic/",
            params=MatchByParameters(
                championship_id=championship_id,
                manager_id=manager_id,
                stadium_id=stadium_id,
                page=page,
                language=self._get_language(language),
            ),
            headers=self._header_provider(),
            response_model=MatchByBasicResponse,
        )

    def get_by_filter_full(
        self,
        championship_id: Optional[str] = None,
        manager_id: Optional[str] = None,
        stadium_id: Optional[str] = None,
        page: Optional[int] = None,
        language: Optional[str] = None,
    ) -> MatchByFullResponse:
        return self.client.do_request(
            endpoint="/matches/by/full/",
            params=MatchByParameters(
                championship_id=championship_id,
                manager_id=manager_id,
                stadium_id=stadium_id,
                page=page,
                language=self._get_language(language),
            ),
            headers=self._header_provider(),
            response_model=MatchByFullResponse,
        )
