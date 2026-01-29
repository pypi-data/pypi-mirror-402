from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional


class BaseParameters(BaseModel):
    """Base model for Soccer Football Info API request parameters.
    
    Provides parameter validation and serialization for API requests.
    Uses short parameter names as per API specification.
    """
    
    model_config = ConfigDict(
        populate_by_name=True,
    )

    @model_validator(mode='before')
    @classmethod
    def remove_none_values(cls, data):
        """Remove None values from input data before model validation."""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data

    def to_dict(self) -> dict:
        """Serialize model to dictionary for API requests.
        
        Returns:
            Dictionary with parameter names suitable for API requests
        """
        return self.model_dump(by_alias=True, exclude_none=True, mode='json')


class ChampionshipListParameters(BaseParameters):
    """Parameters for championships list endpoint.
    
    Attributes:
        page: Page number for pagination (default: 1)
        country: Country code filter (default: "all")
        language: Language code for response (default: en_US)
    """
    page: Optional[int] = Field(default=None, alias="p")
    country: Optional[str] = Field(default=None, alias="c")
    language: Optional[str] = Field(default=None, alias="l")


class ChampionshipViewParameters(BaseParameters):
    """Parameters for championship view endpoint.
    
    Attributes:
        id: Championship ID (required)
        language: Language code for response (default: en_US)
    """
    id: str = Field(alias="i")
    language: Optional[str] = Field(default=None, alias="l")


# =============================================================================
# Matches Parameters
# =============================================================================

class MatchViewParameters(BaseParameters):
    """Parameters for match view endpoints (/matches/view/basic/, /matches/view/full/).
    
    Attributes:
        id: Match ID (required)
        language: Language code for response
    """
    id: str = Field(alias="i")
    language: Optional[str] = Field(default=None, alias="l")


class MatchOddsParameters(BaseParameters):
    """Parameters for match odds endpoint (/matches/odds/).
    
    Attributes:
        id: Match ID (required)
    """
    id: str = Field(alias="i")


class MatchProgressiveParameters(BaseParameters):
    """Parameters for match progressive endpoint (/matches/view/progressive/).
    
    Attributes:
        id: Match ID (required)
        language: Language code for response
        format: Response format ('json' or 'csv')
    """
    id: str = Field(alias="i")
    language: Optional[str] = Field(default=None, alias="l")
    format: Optional[str] = Field(default=None, alias="f")


class MatchDayParameters(BaseParameters):
    """Parameters for match day endpoints (/matches/day/basic/, /matches/day/full/).
    
    Attributes:
        date: Date in ISO format without separator (YYYYMMDD)
        page: Page number for pagination
        language: Language code for response
        format: Response format ('json' or 'csv')
    """
    date: str = Field(alias="d")
    page: Optional[int] = Field(default=None, alias="p")
    language: Optional[str] = Field(default=None, alias="l")
    format: Optional[str] = Field(default=None, alias="f")


class MatchByParameters(BaseParameters):
    """Parameters for match filter endpoints (/matches/by/basic/, /matches/by/full/).
    
    Attributes:
        championship_id: Championship ID filter
        manager_id: Manager ID filter
        stadium_id: Stadium ID filter
        page: Page number for pagination
        language: Language code for response
    """
    championship_id: Optional[str] = Field(default=None, alias="c")
    manager_id: Optional[str] = Field(default=None, alias="m")
    stadium_id: Optional[str] = Field(default=None, alias="s")
    page: Optional[int] = Field(default=None, alias="p")
    language: Optional[str] = Field(default=None, alias="l")


# =============================================================================
# Countries Parameters
# =============================================================================

class CountryListParameters(BaseParameters):
    """Parameters for countries list endpoint (/countries/list/).
    
    Attributes:
        format: Response format ('json' or 'csv')
    """
    format: Optional[str] = Field(default=None, alias="f")
