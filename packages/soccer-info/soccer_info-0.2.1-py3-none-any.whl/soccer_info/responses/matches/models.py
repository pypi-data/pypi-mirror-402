from typing import List, Optional, Any
from pydantic import Field, field_validator

from ..base import ResponseComponent, APIResponse


# =============================================================================
# Basic Match Components
# =============================================================================

class MatchChampionship(ResponseComponent):
    """Championship reference in match data."""
    id: Optional[str] = None
    name: Optional[str] = None
    s_name: Optional[str] = Field(default=None, description="Season name")


class MatchScore(ResponseComponent):
    """Team score breakdown by period."""
    f: Optional[str] = Field(default=None, description="Final score")
    first_half: Optional[str] = Field(default=None, alias="1h", description="First half score")
    second_half: Optional[str] = Field(default=None, alias="2h", description="Second half score")
    overtime: Optional[str] = Field(default=None, alias="o", description="Overtime score")
    penalties: Optional[str] = Field(default=None, alias="p", description="Penalties score")


class MatchAttacks(ResponseComponent):
    """Team attack statistics."""
    n: Optional[str] = Field(default=None, description="Normal attacks")
    d: Optional[str] = Field(default=None, description="Dangerous attacks")
    o_s: Optional[str] = Field(default=None, description="Offsides")


class MatchShoots(ResponseComponent):
    """Team shooting statistics."""
    t: Optional[str] = Field(default=None, description="Total shots")
    off: Optional[str] = Field(default=None, description="Shots off target")
    on: Optional[str] = Field(default=None, description="Shots on target")
    g_a: Optional[str] = Field(default=None, description="Goal attempts")


class MatchCorners(ResponseComponent):
    """Team corner statistics."""
    t: Optional[str] = Field(default=None, description="Total corners")
    f: Optional[str] = Field(default=None, description="First half corners")
    h: Optional[str] = Field(default=None, description="Second half corners")


class MatchFouls(ResponseComponent):
    """Team foul statistics."""
    t: Optional[str] = Field(default=None, description="Total fouls")
    y_c: Optional[str] = Field(default=None, description="Yellow cards")
    y_t_r_c: Optional[str] = Field(default=None, description="Yellow to red cards")
    r_c: Optional[str] = Field(default=None, description="Red cards")


class MatchStats(ResponseComponent):
    """Team match statistics."""
    possession: Optional[str] = None
    attacks: Optional[MatchAttacks] = None
    shoots: Optional[MatchShoots] = None
    penalties: Optional[str] = None
    corners: Optional[MatchCorners] = None
    fouls: Optional[MatchFouls] = None
    substitutions: Optional[str] = None
    throwins: Optional[str] = None
    injuries: Optional[str] = None


class MatchManager(ResponseComponent):
    """Manager/coach reference."""
    id: Optional[str] = None
    name: Optional[str] = None


class MatchTeam(ResponseComponent):
    """Team data in match response."""
    id: Optional[str] = None
    name: Optional[str] = None
    score: Optional[MatchScore] = None
    stats: Optional[MatchStats] = None
    lineup: List[Any] = Field(default_factory=list)
    manager: Optional[MatchManager] = None


class MatchEvent(ResponseComponent):
    """Match event (goal, card, substitution, etc.)."""
    type: Optional[str] = None
    timer: Optional[str] = None
    team: Optional[str] = None
    player: Optional[str] = None
    assist: Optional[str] = None


class MatchReferee(ResponseComponent):
    """Referee reference."""
    id: Optional[str] = None
    name: Optional[str] = None


class MatchStadium(ResponseComponent):
    """Stadium reference."""
    id: Optional[str] = None
    name: Optional[str] = None


# =============================================================================
# Odds Components
# =============================================================================

class Odds1X2(ResponseComponent):
    """1X2 (win/draw/win) odds."""
    home: Optional[str] = Field(default=None, alias="1", description="Home win odds")
    draw: Optional[str] = Field(default=None, alias="X", description="Draw odds")
    away: Optional[str] = Field(default=None, alias="2", description="Away win odds")


class OddsHandicap(ResponseComponent):
    """Asian handicap odds."""
    home: Optional[str] = Field(default=None, alias="1", description="Home odds")
    away: Optional[str] = Field(default=None, alias="2", description="Away odds")
    v: Optional[str] = Field(default=None, description="Handicap value")


class OddsOverUnder(ResponseComponent):
    """Over/under odds."""
    o: Optional[str] = Field(default=None, description="Over odds")
    u: Optional[str] = Field(default=None, description="Under odds")
    v: Optional[str] = Field(default=None, description="Line value")


class BookmakerOdds1X2(ResponseComponent):
    """1X2 odds from multiple bookmakers."""
    bet365: Optional[Odds1X2] = None
    unibet: Optional[Odds1X2] = None


class BookmakerOddsHandicap(ResponseComponent):
    """Handicap odds from multiple bookmakers."""
    bet365: Optional[OddsHandicap] = None
    unibet: Optional[OddsHandicap] = None


class BookmakerOddsOverUnder(ResponseComponent):
    """Over/under odds from multiple bookmakers."""
    bet365: Optional[OddsOverUnder] = None
    unibet: Optional[OddsOverUnder] = None


class MatchOddsSet(ResponseComponent):
    """Complete set of odds for a match moment (kickoff or live)."""
    one_x_two: Optional[BookmakerOdds1X2] = Field(default=None, alias="1X2")
    asian_handicap: Optional[BookmakerOddsHandicap] = None
    over_under: Optional[BookmakerOddsOverUnder] = None
    asian_corner: Optional[BookmakerOddsOverUnder] = None
    first_half_asian_handicap: Optional[BookmakerOddsHandicap] = Field(default=None, alias="1h_asian_handicap")
    first_half_goalline: Optional[BookmakerOddsOverUnder] = Field(default=None, alias="1h_goalline")
    first_half_asian_corner: Optional[BookmakerOddsOverUnder] = Field(default=None, alias="1h_asian_corner")
    first_half_result: Optional[BookmakerOdds1X2] = Field(default=None, alias="1h_result")


class MatchOdds(ResponseComponent):
    """Complete match odds with kickoff and live data."""
    kickoff: Optional[MatchOddsSet] = None
    live: Optional[MatchOddsSet] = None


# =============================================================================
# Progressive Data Components
# =============================================================================

class ProgressiveDataPoint(ResponseComponent):
    """Single data point in progressive match data."""
    timer: Optional[str] = None
    teamA_goal: Optional[str] = None
    teamB_goal: Optional[str] = None
    teamA_possession: Optional[str] = None
    teamB_possession: Optional[str] = None
    teamA_attacks_n: Optional[str] = None
    teamB_attacks_n: Optional[str] = None
    teamA_attacks_d: Optional[str] = None
    teamB_attacks_d: Optional[str] = None
    teamA_off_sides: Optional[str] = None
    teamB_off_sides: Optional[str] = None
    teamA_shoots: Optional[str] = None
    teamB_shoots: Optional[str] = None
    teamA_shoots_on_target: Optional[str] = None
    teamB_shoots_on_target: Optional[str] = None
    teamA_shoots_off_target: Optional[str] = None
    teamB_shoots_off_target: Optional[str] = None
    teamA_corners: Optional[str] = None
    teamB_corners: Optional[str] = None
    teamA_fouls: Optional[str] = None
    teamB_fouls: Optional[str] = None
    teamA_yellow_cards: Optional[str] = None
    teamB_yellow_cards: Optional[str] = None
    teamA_red_cards: Optional[str] = None
    teamB_red_cards: Optional[str] = None
    # Odds data
    odd_1x2_1: Optional[str] = None
    odd_1x2_X: Optional[str] = None
    odd_1x2_2: Optional[str] = None
    odd_asian_handicap_1: Optional[str] = None
    odd_asian_handicap_2: Optional[str] = None
    odd_asian_handicap_v: Optional[str] = None
    odd_over_under_o: Optional[str] = None
    odd_over_under_u: Optional[str] = None
    odd_over_under_v: Optional[str] = None


class ProgressiveMatch(ResponseComponent):
    """Match with progressive data points."""
    id: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None
    championship: Optional[MatchChampionship] = None
    teamA: Optional[MatchTeam] = None
    teamB: Optional[MatchTeam] = None
    data: List[ProgressiveDataPoint] = Field(default_factory=list)


# =============================================================================
# Match Types
# =============================================================================

class MatchBasic(ResponseComponent):
    """Match with basic data (no odds)."""
    id: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None
    timer: Optional[str] = None
    est_e_timer: Optional[str] = Field(default=None, description="Estimated extra time")
    championship: Optional[MatchChampionship] = None
    teamA: Optional[MatchTeam] = None
    teamB: Optional[MatchTeam] = None
    events: List[MatchEvent] = Field(default_factory=list)
    referee: Optional[MatchReferee] = None
    stadium: Optional[MatchStadium] = None


class MatchFull(ResponseComponent):
    """Match with full data including odds."""
    id: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None
    timer: Optional[str] = None
    est_e_timer: Optional[str] = Field(default=None, description="Estimated extra time")
    championship: Optional[MatchChampionship] = None
    teamA: Optional[MatchTeam] = None
    teamB: Optional[MatchTeam] = None
    events: List[MatchEvent] = Field(default_factory=list)
    referee: Optional[MatchReferee] = None
    stadium: Optional[MatchStadium] = None
    odds: Optional[MatchOdds] = None
    
    @field_validator('odds', mode='before')
    @classmethod
    def convert_empty_list_to_none(cls, value):
        """Convert empty list to None for odds field.
        
        The API sometimes returns [] instead of None when odds data is not available.
        """
        if isinstance(value, list) and not value:
            return None
        return value


# =============================================================================
# Response Types
# =============================================================================

class MatchViewBasicResponse(APIResponse[MatchBasic]):
    """Response for /matches/view/basic/ endpoint."""
    pass


class MatchViewFullResponse(APIResponse[MatchFull]):
    """Response for /matches/view/full/ endpoint."""
    pass


class MatchOddsResponse(APIResponse[MatchOdds]):
    """Response for /matches/odds/ endpoint."""
    pass


class MatchProgressiveResponse(APIResponse[ProgressiveMatch]):
    """Response for /matches/view/progressive/ endpoint."""
    pass


class MatchDayBasicResponse(APIResponse[MatchBasic]):
    """Response for /matches/day/basic/ endpoint."""
    pass


class MatchDayFullResponse(APIResponse[MatchFull]):
    """Response for /matches/day/full/ endpoint."""
    pass


class MatchByBasicResponse(APIResponse[MatchBasic]):
    """Response for /matches/by/basic/ endpoint."""
    pass


class MatchByFullResponse(APIResponse[MatchFull]):
    """Response for /matches/by/full/ endpoint."""
    pass
