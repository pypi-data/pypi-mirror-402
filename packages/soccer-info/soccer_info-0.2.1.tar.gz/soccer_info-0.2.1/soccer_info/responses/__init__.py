"""Response models for Soccer Football Info API."""
from .base import ResponseComponent, APIResponse, Pagination, ResponseHeaders
from .championships import (
    ChampionshipListItem,
    ChampionshipListResponse,
    ChampionshipDetail,
    ChampionshipViewResponse,
    Season,
    Group,
    TableEntry,
    Team,
)
from .matches import (
    # Basic components
    MatchChampionship,
    MatchScore,
    MatchAttacks,
    MatchShoots,
    MatchCorners,
    MatchFouls,
    MatchStats,
    MatchManager,
    MatchTeam,
    MatchEvent,
    MatchReferee,
    MatchStadium,
    # Odds components
    Odds1X2,
    OddsHandicap,
    OddsOverUnder,
    BookmakerOdds1X2,
    BookmakerOddsHandicap,
    BookmakerOddsOverUnder,
    MatchOddsSet,
    MatchOdds,
    # Progressive data
    ProgressiveDataPoint,
    ProgressiveMatch,
    # Match types
    MatchBasic,
    MatchFull,
    # Response types
    MatchViewBasicResponse,
    MatchViewFullResponse,
    MatchOddsResponse,
    MatchProgressiveResponse,
    MatchDayBasicResponse,
    MatchDayFullResponse,
    MatchByBasicResponse,
    MatchByFullResponse,
)
from .countries import (
    CountryItem,
    CountryListResponse,
)

__all__ = [
    # Base
    'ResponseComponent',
    'APIResponse',
    'Pagination',
    'ResponseHeaders',
    # Championships
    'ChampionshipListItem',
    'ChampionshipListResponse',
    'ChampionshipDetail',
    'ChampionshipViewResponse',
    'Season',
    'Group',
    'TableEntry',
    'Team',
    # Matches - Basic components
    'MatchChampionship',
    'MatchScore',
    'MatchAttacks',
    'MatchShoots',
    'MatchCorners',
    'MatchFouls',
    'MatchStats',
    'MatchManager',
    'MatchTeam',
    'MatchEvent',
    'MatchReferee',
    'MatchStadium',
    # Matches - Odds components
    'Odds1X2',
    'OddsHandicap',
    'OddsOverUnder',
    'BookmakerOdds1X2',
    'BookmakerOddsHandicap',
    'BookmakerOddsOverUnder',
    'MatchOddsSet',
    'MatchOdds',
    # Matches - Progressive data
    'ProgressiveDataPoint',
    'ProgressiveMatch',
    # Matches - Match types
    'MatchBasic',
    'MatchFull',
    # Matches - Response types
    'MatchViewBasicResponse',
    'MatchViewFullResponse',
    'MatchOddsResponse',
    'MatchProgressiveResponse',
    'MatchDayBasicResponse',
    'MatchDayFullResponse',
    'MatchByBasicResponse',
    'MatchByFullResponse',
    # Countries
    'CountryItem',
    'CountryListResponse',
]
