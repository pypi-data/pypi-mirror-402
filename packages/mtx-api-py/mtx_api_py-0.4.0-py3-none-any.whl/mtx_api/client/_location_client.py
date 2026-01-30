from mtx_api.client._mtx_http_client import Method, MtxHttpClient
from mtx_api.models.additional_data import LocationAdditionalDataList
from mtx_api.models.errors import MissingJurisdictionElementIdError


class LocationClient:
    def __init__(self, client: MtxHttpClient):
        self.client: MtxHttpClient = client

    async def resolve(
        self,
        *,
        jurisdiction_element_id: str,
        formatted_address: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
    ) -> LocationAdditionalDataList:
        """
        Retrieves latitude and longitude information from an address, or vice versa.

        This tool fetches location-specific questions configured for a
        jurisdiction element. You can identify the location by providing either a formatted
        address, geographic coordinates (lat, lng), or both. Regardless of which parameters
        you provide, the tool always returns the complete location information including
        formatted address, geographic coordinates, and the list of additional data questions.

        Use this tool when you need to know what additional information should be collected
        for a specific location.

        Args:
            jurisdiction_element_id: The unique identifier string of the jurisdiction element
                where the location is being queried.
            formatted_address: Optional complete address string in human-readable format
                to identify the location.
            lat: Optional latitude coordinate as a decimal number to identify the location.
                Must be provided together with lng.
            lng: Optional longitude coordinate as a decimal number to identify the location.
                Must be provided together with lat.

        Returns:
            LocationAdditionalDataList: A collection of location entries. Each entry always
                contains the formatted address, geographic coordinates (latitude and longitude),
                and a list of additional data questions configured for that location, regardless
                of which input parameters were used to identify the location.

        Raises:
            MissingJurisdictionElementIdError: If jurisdiction_element_id is empty or not provided.
        """
        if not jurisdiction_element_id:
            raise MissingJurisdictionElementIdError()
        return await self.client.http_request(
            method=Method.GET,
            path="location-additional-data",
            model=LocationAdditionalDataList,
            query_params={
                "jurisdiction_element_id": jurisdiction_element_id,
                "formatted_address": formatted_address,
                "lat": lat,
                "lng": lng,
            },
        )
