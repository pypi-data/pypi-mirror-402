from mtx_api.client._mtx_http_client import (
    Method,
    MtxHttpClient,
)
from mtx_api.models.errors import MissingJurisdictionCodesError
from mtx_api.models.typology import TypologyList


class TypologyClient:
    def __init__(self, client: MtxHttpClient):
        self._client: MtxHttpClient = client

    async def list(
        self,
        *,
        access_token: str | None = None,
        jurisdiction_codes: list[str],
        jurisdiction_element_id: str | None = None,
        typology_ids: list[str] | None = None,
        lat: float | None = None,
        lng: float | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> TypologyList:
        """
        Retrieve a list of typologies from the platform based on jurisdiction codes.

        This tool fetches typologies available for the specified jurisdiction codes,
        optionally filtering by specific typology IDs, jurisdiction element, or location.

        Args:
            access_token (str, opcional): Optional token used for authentication. If not provided, the operation
                will be made without authentication. Defaults to None.
            jurisdiction_codes (list[str]): List of jurisdiction codes used to filter the typologies.
            jurisdiction_element_id (str, opcional): Optional ID of a specific jurisdiction element
                to filter results. Defaults to None.
            typology_ids (list[str], opcional): Optional list of specific typology IDs to retrieve.
                Defaults to None.
            lat (float, opcional): Optional latitude coordinate for location-based filtering.
                Defaults to None.
            lng (float, opcional): Optional longitude coordinate for location-based filtering.
                Defaults to None.
            page (int, opcional): Optional page number for result pagination. Defaults to None.
            limit (int, opcional): Optional maximum number of items to return per page.
                Defaults to None.

        Returns:
            TypologyList: A collection of typology items matching the specified criteria.

        Raises:
            MissingJurisdictionCodesError: If `jurisdiction_codes` is empty.
        """
        if not jurisdiction_codes:
            raise MissingJurisdictionCodesError()
        return await self._client.http_request(
            method=Method.GET,
            path="typologies",
            model=TypologyList,
            access_token=access_token,
            query_params={
                "jurisdiction_ids": jurisdiction_codes,
                "jurisdiction_element_id": jurisdiction_element_id,
                "typology_ids": typology_ids,
                "lng": lng,
                "lat": lat,
                "page": page,
                "limit": limit,
            },
        )
