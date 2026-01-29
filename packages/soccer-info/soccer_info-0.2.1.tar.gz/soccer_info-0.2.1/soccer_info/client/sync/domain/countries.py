from dataclasses import dataclass
from typing import Optional

from soccer_info.requests_ import CountryListParameters
from soccer_info.responses import CountryListResponse
from ..client import Client
from ...common.domain.countries import Countries as CommonCountries


@dataclass
class Countries(CommonCountries):
    """Synchronous domain client for country-related API endpoints."""

    client: Client

    def get_list(
        self,
        format_: Optional[str] = None,
    ) -> CountryListResponse:
        return self.client.do_request(
            endpoint="/countries/list/",
            params=CountryListParameters(
                format=format_,
            ),
            headers=self._header_provider(),
            response_model=CountryListResponse,
        )
