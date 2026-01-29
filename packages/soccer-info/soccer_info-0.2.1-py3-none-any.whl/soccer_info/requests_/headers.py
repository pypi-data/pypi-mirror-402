from pydantic import BaseModel, ConfigDict, Field, model_validator


class Header(BaseModel):
    """HTTP header model for RapidAPI Soccer Football Info requests.
    
    Provides HTTP header abstraction with RapidAPI authentication.
    Includes security features for API key masking in logs.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )

    x_rapidapi_key: str = Field(alias="X-RapidAPI-Key")
    x_rapidapi_host: str = Field(
        default="soccer-football-info.p.rapidapi.com",
        alias="X-RapidAPI-Host"
    )

    @model_validator(mode='before')
    @classmethod
    def remove_none_values(cls, data):
        """Remove None values from input data before model validation."""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data

    def to_dict(self, mask: bool = False) -> dict:
        """Serialize model to dictionary for HTTP requests.
        
        Args:
            mask: If True, replaces API key with asterisks for secure logging
            
        Returns:
            Dictionary with properly formatted HTTP headers
        """
        data = self.model_dump(by_alias=True)
        if mask:
            data['X-RapidAPI-Key'] = "*" * len(data['X-RapidAPI-Key'])
        return data
