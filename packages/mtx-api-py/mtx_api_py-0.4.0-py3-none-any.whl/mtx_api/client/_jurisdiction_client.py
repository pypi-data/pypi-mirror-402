from __future__ import annotations

from mtx_api.client._mtx_http_client import Method, MtxHttpClient
from mtx_api.models.errors import MissingJurisdictionCodesError
from mtx_api.models.jurisdiction import Jurisdiction, JurisdictionList


class JurisdictionClient:
    def __init__(self, client: MtxHttpClient):
        self._client: MtxHttpClient = client

    async def list(
        self,
        *,
        access_token: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> JurisdictionList:
        """Retrieves a list of jurisdictions from the platform.

        This tool allows you to list all available jurisdictions or find those closest to a
        specific location if coordinates are provided.

        Args:
            access_token: Optional token used for authentication. If not provided,
                the operation will be made without authentication.
            lat: Optional latitude coordinate to filter jurisdictions by proximity.
            lng: Optional longitude coordinate to filter jurisdictions by proximity.

        Returns:
            JurisdictionList: A collection of Jurisdiction objects with basic details.
        """
        return await self._client.http_request(
            method=Method.GET,
            path="jurisdictions",
            model=JurisdictionList,
            access_token=access_token,
            query_params={
                "lat": lat,
                "long": lng,
            },
        )

    async def detail(
        self,
        *,
        access_token: str | None = None,
        jurisdiction_code: str,
    ) -> Jurisdiction:
        """Retrieves detailed information for a specific jurisdiction.

        This tool fetches the complete details of a jurisdiction using its unique code.
        Use this tool when you need more information about a specific jurisdiction than what is
        provided in the list.

        Args:
            access_token: Optional token used for authentication. If not provided,
                the operation will be made without authentication.
            jurisdiction_code: The unique string code of the jurisdiction to query.

        Raises:
            MissingJurisdictionCodesError: If the provided jurisdiction_code is empty.

        Returns:
            Jurisdiction: An object containing comprehensive information about the jurisdiction.
        """
        if not jurisdiction_code:
            raise MissingJurisdictionCodesError()
        return await self._client.http_request(
            method=Method.GET,
            path=f"jurisdictions/{jurisdiction_code}",
            model=Jurisdiction,
            access_token=access_token,
        )
