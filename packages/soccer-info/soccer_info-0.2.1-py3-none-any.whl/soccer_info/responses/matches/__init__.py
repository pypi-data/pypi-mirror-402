"""Response models for matches endpoints."""
from .models import (
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

__all__ = [
    # Basic components
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
    # Odds components
    'Odds1X2',
    'OddsHandicap',
    'OddsOverUnder',
    'BookmakerOdds1X2',
    'BookmakerOddsHandicap',
    'BookmakerOddsOverUnder',
    'MatchOddsSet',
    'MatchOdds',
    # Progressive data
    'ProgressiveDataPoint',
    'ProgressiveMatch',
    # Match types
    'MatchBasic',
    'MatchFull',
    # Response types
    'MatchViewBasicResponse',
    'MatchViewFullResponse',
    'MatchOddsResponse',
    'MatchProgressiveResponse',
    'MatchDayBasicResponse',
    'MatchDayFullResponse',
    'MatchByBasicResponse',
    'MatchByFullResponse',
]
