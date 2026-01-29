from typing import List, Optional
from pydantic import Field

from ..base import ResponseComponent, APIResponse


class CountryItem(ResponseComponent):
    """Country item in list response."""
    code: Optional[str] = Field(default=None, description="Country code (e.g., 'IT', 'ES')")
    name: Optional[str] = None
    timezones: List[str] = Field(default_factory=list)
    championships: Optional[int] = Field(default=None, description="Number of championships")
    managers: Optional[int] = Field(default=None, description="Number of managers")
    players: Optional[int] = Field(default=None, description="Number of players")
    referees: Optional[int] = Field(default=None, description="Number of referees")
    stadiums: Optional[int] = Field(default=None, description="Number of stadiums")
    teams: Optional[int] = Field(default=None, description="Number of teams")


class CountryListResponse(APIResponse[CountryItem]):
    """Response for /countries/list/ endpoint."""
    pass
