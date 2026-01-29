from pydantic import BaseModel


class Settings(BaseModel):
    """Core configuration for Soccer Football Info API client.
    
    Contains authentication credentials and configuration settings
    used by all API client operations.
    """
    api_key: str
    api_host: str = "soccer-football-info.p.rapidapi.com"
    base_url: str = "https://soccer-football-info.p.rapidapi.com"
    request_throttle_seconds: float = 0.3  # Minimum seconds between API requests
    request_timeout: float = 30
