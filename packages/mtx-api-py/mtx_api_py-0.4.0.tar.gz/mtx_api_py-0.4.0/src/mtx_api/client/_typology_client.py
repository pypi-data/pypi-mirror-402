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
        """Retrieve a list of typologies from the platform based on jurisdiction codes.

        This tool fetches typologies available for the specified jurisdiction codes,
        optionally filtering by specific typology IDs, jurisdiction element, or location.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.
            jurisdiction_codes: List of jurisdiction codes used to filter the typologies.
            jurisdiction_element_id: Optional ID of a specific jurisdiction element to filter
                results.
            typology_ids: Optional list of specific typology IDs to retrieve.
            lat: Optional latitude coordinate for location-based filtering.
            lng: Optional longitude coordinate for location-based filtering.
            page: Optional page number for result pagination.
            limit: Optional maximum number of items to return per page.

        Raises:
            MissingJurisdictionCodesError: If `jurisdiction_codes` is empty.

        Returns:
            TypologyList: A collection of typology items matching the specified criteria.
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
