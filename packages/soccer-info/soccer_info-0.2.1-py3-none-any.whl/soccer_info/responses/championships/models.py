from typing import List, Optional
from pydantic import Field

from ..base import ResponseComponent, APIResponse


class Team(ResponseComponent):
    """Team reference in standings table."""
    id: str
    name: str


class TableEntry(ResponseComponent):
    """Single entry in a league standings table."""
    team: Team  # Team has required fields internally
    position: Optional[int] = None
    win: Optional[int] = None
    draw: Optional[int] = None
    loss: Optional[int] = None
    points: Optional[int] = None
    goals_scored: Optional[int] = None
    goals_conceded: Optional[int] = None
    note: Optional[str] = None

    @property
    def matches_played(self) -> Optional[int]:
        """Calculate total matches played."""
        if self.win is not None and self.draw is not None and self.loss is not None:
            return self.win + self.draw + self.loss
        return None

    @property
    def goal_difference(self) -> Optional[int]:
        """Calculate goal difference."""
        if self.goals_scored is not None and self.goals_conceded is not None:
            return self.goals_scored - self.goals_conceded
        return None


class Group(ResponseComponent):
    """Group/league within a championship season."""
    name: Optional[str] = None
    table: List[TableEntry] = Field(default_factory=list)


class Season(ResponseComponent):
    """Championship season with date range and standings."""
    name: Optional[str] = None
    from_date: Optional[str] = Field(default=None, alias="from")
    to_date: Optional[str] = Field(default=None, alias="to")
    groups: List[Group] = Field(default_factory=list)


class ChampionshipListItem(ResponseComponent):
    """Championship item in list response."""
    id: Optional[str] = None
    name: Optional[str] = None
    has_image: Optional[bool] = None


class ChampionshipDetail(ResponseComponent):
    """Detailed championship data with seasons."""
    id: Optional[str] = None
    name: Optional[str] = None
    country: Optional[str] = None
    has_image: Optional[bool] = None
    seasons: List[Season] = Field(default_factory=list)


class ChampionshipListResponse(APIResponse[ChampionshipListItem]):
    """Response for championships list endpoint."""
    pass


class ChampionshipViewResponse(APIResponse[ChampionshipDetail]):
    """Response for championship view endpoint."""
    pass
