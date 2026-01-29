from dataclasses import dataclass
from typing import Optional

from soccer_info.requests_ import CountryListParameters
from soccer_info.responses import CountryListResponse
from ..async_client import AsyncClient
from ...common.domain.countries import Countries as CommonCountries


@dataclass
class AsyncCountries(CommonCountries):
    """Asynchronous domain client for country-related API endpoints."""

    client: AsyncClient

    async def get_list(
        self,
        format: Optional[str] = None,
    ) -> CountryListResponse:
        return await self.client.do_request(
            endpoint="/countries/list/",
            params=CountryListParameters(
                format=format,
            ),
            headers=self._header_provider(),
            response_model=CountryListResponse,
        )
