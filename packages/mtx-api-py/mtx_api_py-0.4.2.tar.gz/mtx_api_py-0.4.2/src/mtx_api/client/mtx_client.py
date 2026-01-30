from __future__ import annotations

import httpx

from mtx_api._doc import get_documentation
from mtx_api.client._auth_client import AuthClient
from mtx_api.client._base_client import BaseClient
from mtx_api.client._jurisdiction_client import JurisdictionClient
from mtx_api.client._jurisdiction_elements_client import JurisdictionElementsClient
from mtx_api.client._location_client import LocationClient
from mtx_api.client._mtx_http_client import MtxHttpClient
from mtx_api.client._request_client import RequestClient
from mtx_api.client._service_client import ServiceClient
from mtx_api.client._typology_client import TypologyClient
from mtx_api.client._user_client import UserClient


class MTXClient:
    def __init__(
        self,
        base_url: str | None = None,
        client_id: str | None = None,
        jwt_secret: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._http_client = MtxHttpClient(
            base_url=base_url,
            client_id=client_id,
            jwt_secret=jwt_secret,
            transport=transport,
        )
        self.base = BaseClient(self._http_client)
        self.auth = AuthClient(self._http_client)
        self.user = UserClient(self._http_client)
        self.location = LocationClient(self._http_client)
        self.services = ServiceClient(self._http_client)
        self.typologies = TypologyClient(self._http_client)
        self.jurisdictions = JurisdictionClient(self._http_client)
        self.jurisdiction_elements = JurisdictionElementsClient(self._http_client)
        self.requests = RequestClient(self._http_client)

    async def __aenter__(self) -> MTXClient:
        await self._http_client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        await self._http_client.__aexit__(exc_type, exc, tb)

    @staticmethod
    def get_documentation() -> str:
        """Returns a Markdown string with the documentation for all MTX Client functions."""
        return get_documentation()
