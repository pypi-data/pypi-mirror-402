from mtx_api.client._mtx_http_client import (
    Method,
    MtxHttpClient,
)
from mtx_api.models.errors import MissingJurisdictionCodesError, MissingServiceIdError
from mtx_api.models.service import Service, ServiceList


class ServiceClient:
    def __init__(self, client: MtxHttpClient):
        self._client: MtxHttpClient = client

    async def list(
        self,
        *,
        access_token: str | None = None,
        jurisdiction_codes: list[str],
        lat: float | None = None,
        lng: float | None = None,
        typology_ids: list[str] | None = None,
    ) -> ServiceList:
        """Retrieves a list of services available in the specified jurisdictions.

        This function allows searching for services filtering by jurisdiction codes,
        and optionally by geographic location (latitude and longitude) or typology identifiers.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.
            jurisdiction_codes: List of jurisdiction codes to filter the services.
            lat: Optional latitude for geolocation filtering.
            lng: Optional longitude for geolocation filtering.
            typology_ids: Optional list of typology identifiers to filter the services.

        Raises:
            MissingJurisdictionCodesError: If the list of jurisdiction codes is empty.

        Returns:
            The list of services matching the specified criteria.
        """
        if not jurisdiction_codes:
            raise MissingJurisdictionCodesError()
        return await self._client.http_request(
            method=Method.GET,
            path="services",
            model=ServiceList,
            access_token=access_token,
            query_params={
                "jurisdiction_ids": jurisdiction_codes,
                "lat": lat,
                "lng": lng,
                "typology_ids": typology_ids,
            },
        )

    async def detail(
        self,
        *,
        access_token: str | None = None,
        service_id: str,
        jurisdiction_code: str,
    ) -> Service:
        """Retrieves the detailed information of a specific service.

        This function fetches the full details of a service identified by its ID
        within a specific jurisdiction. Details include additional_data and other
        relevant information.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.
            service_id: The identifier of the service to fetch details for.
            jurisdiction_code: The jurisdiction code where the service is located.

        Raises:
            MissingJurisdictionCodesError: If the jurisdiction code is not provided.
            MissingServiceIdError: If the service ID is not provided.

        Returns:
            The detailed information of the requested service.
        """
        if not jurisdiction_code:
            raise MissingJurisdictionCodesError()
        if not service_id:
            raise MissingServiceIdError()
        return await self._client.http_request(
            method=Method.GET,
            path=f"services/{service_id}",
            model=Service,
            access_token=access_token,
            query_params={
                "jurisdiction_id": jurisdiction_code,
            },
        )
