# Soccer Info - Python SDK for Soccer Football Info API

[![PyPI version](https://img.shields.io/pypi/v/soccer-info.svg)](https://pypi.org/project/soccer-info/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/soccer-info.svg)](https://pypi.org/project/soccer-info/)

A Python SDK for accessing the Soccer Football Info API via RapidAPI. Provides both synchronous and asynchronous clients with typed request builders and Pydantic response models for soccer championship data.

## Scope and Limitations

This SDK currently implements **Championships, Countries, and Matches** endpoints from the Soccer Football Info API:

* **Championships** - Browse and filter championships by country, get detailed championship data including seasons, groups, and team standings
* **Countries** - List all countries with soccer data including statistics on championships, teams, players, managers, referees, and stadiums
* **Matches** - Query match data with basic/full details, betting odds from multiple bookmakers, progressive timeline snapshots, and filter by date, championship, manager, or stadium

The Soccer Football Info API offers 29 total endpoints covering live scores, teams, players, managers, referees, stadiums, and more. This SDK currently focuses on championship, country, and match data. For the complete API catalog, visit the [Soccer Football Info API documentation on RapidAPI](https://rapidapi.com/soccerfootball-info-soccerfootball-info-default/api/soccer-football-info).

Future versions may expand to include additional endpoints based on community needs.

## Quick Start

### Installation

```bash
pip install soccer-info
```

### Requirements

- Python 3.13 or higher
- RapidAPI account (free tier available)
- RapidAPI key for Soccer Football Info API

**Get your RapidAPI key:**
1. Sign up at [RapidAPI](https://rapidapi.com/)
2. Subscribe to [Soccer Football Info API](https://rapidapi.com/fluis.lacasse/api/soccer-football-info)
3. Find your API key in the API dashboard

### Basic Usage

```python
import soccer_info

# Create client with default settings (uses RAPIDAPI_SOCCER_INFO_KEY env var)
client = soccer_info.quick_client()

# Get list of championships
championships = client.championships.get_list()
print(f"Found {len(championships.result)} championships")

# Get detailed championship data
championship_detail = client.championships.get_by_id("5778d8e65b65c7f9")
print(f"Championship: {championship_detail.first_result.name}")
print(f"Country: {championship_detail.first_result.country}")
```

## API Key Setup

The SDK provides multiple flexible ways to configure your RapidAPI key:

#### Quick Start (Default)

Set the `RAPIDAPI_SOCCER_INFO_KEY` environment variable and use `quick_client()`:

```python
import soccer_info

client = soccer_info.quick_client()
championships = client.championships.get_list()
```

#### All Configuration Options

**1. Environment Variable (Default)**

```python
import soccer_info

# Uses RAPIDAPI_SOCCER_INFO_KEY environment variable
client = soccer_info.quick_client()
```

**2. Direct API Key**

```python
from soccer_info.settings import SettingsBuilder
import soccer_info

settings = SettingsBuilder().with_api_key(key="your-rapidapi-key-here").build()
client = soccer_info.quick_client(settings)
```

**3. Custom Environment Variable**

```python
from soccer_info.settings import SettingsBuilder
import soccer_info

settings = SettingsBuilder().with_api_key(environment="MY_CUSTOM_API_KEY").build()
client = soccer_info.quick_client(settings)
```

**4. Provider Function**

```python
from soccer_info.settings import SettingsBuilder
import soccer_info

def get_api_key():
    # Load from secure vault, file, or other source
    return "your-api-key"

settings = SettingsBuilder().with_api_key(key_provider=get_api_key).build()
client = soccer_info.quick_client(settings)
```

## Advanced Usage

### Custom Client Configuration

```python
from soccer_info.settings import SettingsBuilder
from soccer_info.client import HTTPXClient

# Build custom settings
settings = (
    SettingsBuilder()
    .with_api_key(key="your-api-key")
    .with_base_url("https://soccer-football-info.p.rapidapi.com")
    .with_host("soccer-football-info.p.rapidapi.com")
    .build()
)

# Create client with custom settings
client = HTTPXClient(settings)
championships = client.championships.get_list()
```

### Context Manager for Resource Management

```python
import soccer_info

# Automatically closes HTTP client when done
with soccer_info.quick_client() as client:
    championships = client.championships.get_list()
    for champ in championships.result:
        detail = client.championships.get_by_id(champ.id)
        print(f"{detail.first_result.name}")
```

### Asynchronous Client

The async client includes built-in request throttling to respect API rate limits. See [`settings.py`](soccer_info/settings/settings.py) for default configuration values.

```python
import asyncio
import soccer_info

async def main():
    # Create async client with context manager
    async with soccer_info.quick_async_client() as client:
        # Fetch data asynchronously
        championships = await client.championships.get_list()
        
        # Fetch multiple championships concurrently
        # Throttling is automatically handled
        tasks = [
            client.championships.get_by_id(champ.id)
            for champ in championships.result[:5]
        ]
        results = await asyncio.gather(*tasks)
        
        for detail in results:
            print(f"{detail.first_result.name}")

asyncio.run(main())
```

### Rate Limit Monitoring

```python
import soccer_info

client = soccer_info.quick_client()
response = client.championships.get_list()

# Access rate limit information from response headers
headers = response.response_headers
print(f"Rate limit: {headers.rate_limit_remaining}/{headers.rate_limit_limit}")
print(f"Resets in: {headers.hours_to_reset} hours")
print(f"Resets in: {headers.rate_limit_reset} seconds")
```

### Saving Responses to JSON

```python
from pathlib import Path
import soccer_info

client = soccer_info.quick_client()
response = client.championships.get_list()

# Save full response to JSON file
response.save_pretty_json(Path("championships.json"))

# Save individual championship detail
detail = client.championships.get_by_id("5778d8e65b65c7f9")
detail.save_pretty_json(Path("championship_detail.json"))
```

### Setting Default Language

```python
from soccer_info.settings import SettingsBuilder
from soccer_info.client import HTTPXClient

settings = SettingsBuilder().with_api_key().build()

# Set default language for all requests
client = HTTPXClient(settings, default_language="es_ES")

# Uses Spanish by default
championships = client.championships.get_list()

# Override for specific request
championships_german = client.championships.get_list(language="de_DE")
```

## API Reference

### Client Creation Functions

* `quick_client()` - Create synchronous client with default settings
* `quick_async_client()` - Create asynchronous client with default settings

### Championship Methods

* `get_list(page=None, country=None, language=None)` - Retrieve paginated list of championships with optional country filter
* `get_by_id(championship_id, language=None)` - Get detailed championship data including seasons, groups, and standings

### Countries Methods

* `get_list(format_=None)` - Retrieve list of all countries with soccer data and statistics

### Matches Methods

**Single Match Endpoints:**
* `get_view_basic(match_id, language=None)` - Get single match with basic data (no odds)
* `get_view_full(match_id, language=None)` - Get single match with full data including odds
* `get_odds(match_id)` - Get match odds from multiple bookmakers
* `get_progressive(match_id, language=None, format=None)` - Get match with progressive timeline data

**Day-Based Endpoints:**
* `get_by_day_basic(date, page=None, language=None, format=None)` - Get matches for specific date with basic data
* `get_by_day_full(date, page=None, language=None, format=None)` - Get matches for specific date with full data including odds

**Filter-Based Endpoints:**
* `get_by_filter_basic(championship_id=None, manager_id=None, stadium_id=None, page=None, language=None)` - Filter matches by championship, manager, or stadium (basic data)
* `get_by_filter_full(championship_id=None, manager_id=None, stadium_id=None, page=None, language=None)` - Filter matches by championship, manager, or stadium (full data with odds)

### Response Models

#### Championships Response Models

* `ChampionshipListResponse` - Paginated list of championship items
* `ChampionshipViewResponse` - Detailed championship with seasons and standings
* `ChampionshipListItem` - Basic championship information (id, name, has_image)
* `ChampionshipDetail` - Full championship data with seasons
* `Season` - Season information with date range and groups
* `Group` - League group with standings table
* `TableEntry` - Team standing with position, points, wins, draws, losses, goals
* `Team` - Team reference (id, name)

#### Countries Response Models

* `CountryListResponse` - List of countries with soccer data
* `CountryItem` - Country information with code, name, timezones, and statistics (championships, managers, players, referees, stadiums, teams)

#### Matches Response Models

**Match Types:**
* `MatchBasic` - Match with basic data (no odds)
* `MatchFull` - Match with full data including odds
* `ProgressiveMatch` - Match with progressive timeline data

**Match Components:**
* `MatchChampionship` - Championship reference in match data
* `MatchTeam` - Team data with score, stats, lineup, and manager
* `MatchScore` - Score breakdown by period (final, first half, second half, overtime, penalties)
* `MatchStats` - Team statistics (possession, attacks, shots, corners, fouls)
* `MatchEvent` - Match events (goals, cards, substitutions)
* `MatchReferee` - Referee reference
* `MatchStadium` - Stadium reference

**Odds Components:**
* `MatchOdds` - Complete match odds (kickoff and live)
* `MatchOddsSet` - Set of odds for a match moment
* `Odds1X2` - Win/draw/win odds
* `OddsHandicap` - Asian handicap odds
* `OddsOverUnder` - Over/under odds
* `BookmakerOdds1X2` - 1X2 odds from multiple bookmakers
* `BookmakerOddsHandicap` - Handicap odds from multiple bookmakers
* `BookmakerOddsOverUnder` - Over/under odds from multiple bookmakers

**Progressive Data:**
* `ProgressiveDataPoint` - Single data point in progressive match timeline

**Response Types:**
* `MatchViewBasicResponse` - Response for single match basic view
* `MatchViewFullResponse` - Response for single match full view
* `MatchOddsResponse` - Response for match odds
* `MatchProgressiveResponse` - Response for progressive match data
* `MatchDayBasicResponse` - Response for day-based basic query
* `MatchDayFullResponse` - Response for day-based full query
* `MatchByBasicResponse` - Response for filter-based basic query
* `MatchByFullResponse` - Response for filter-based full query

### Response Properties

All responses include:
* `status` - HTTP status code
* `errors` - List of error messages
* `result` - List of result items
* `pagination` - Pagination information
* `response_headers` - HTTP headers including rate limit info
* `is_success` - Boolean property indicating successful response
* `first_result` - Convenience property for first result item
* `pagination_info` - Convenience property for pagination data

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

We welcome contributions! Here's how you can help:

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/soccer-info.git
   cd soccer-info
   ```
3. **Set up development environment**:
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   
   # Install in development mode with dev dependencies
   pip install -e .
   pip install -r requirements-dev.txt
   ```

### Development Environment

The project includes:
- `python-dotenv` for managing environment variables during development
- Example scripts in the `examples/` directory demonstrating both sync and async usage
- Type checking support with `py.typed` marker

Create a `.env` file in the project root for development:
```
RAPIDAPI_SOCCER_INFO_KEY=your-development-api-key
```

### Project Structure

The SDK follows a clean architecture pattern:

```
soccer_info/
├── __init__.py          # Public API exports and quick_client()
├── py.typed             # PEP 561 type marker
├── client/              # Client implementations (sync/async)
├── requests_/           # Request components (headers, parameters)
├── responses/           # Response models (Pydantic)
└── settings/            # Configuration management
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Document public APIs with docstrings
- Keep response models aligned with API structure

### Code of Conduct

Be respectful and constructive in all interactions. This project follows standard open source community guidelines.

