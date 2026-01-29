"""Request building components for Soccer Football Info API."""
from .headers import Header
from .parameters import (
    BaseParameters,
    ChampionshipListParameters,
    ChampionshipViewParameters,
    MatchViewParameters,
    MatchOddsParameters,
    MatchProgressiveParameters,
    MatchDayParameters,
    MatchByParameters,
    CountryListParameters,
)

__all__ = [
    'Header',
    'BaseParameters',
    # Championships
    'ChampionshipListParameters',
    'ChampionshipViewParameters',
    # Matches
    'MatchViewParameters',
    'MatchOddsParameters',
    'MatchProgressiveParameters',
    'MatchDayParameters',
    'MatchByParameters',
    # Countries
    'CountryListParameters',
]
