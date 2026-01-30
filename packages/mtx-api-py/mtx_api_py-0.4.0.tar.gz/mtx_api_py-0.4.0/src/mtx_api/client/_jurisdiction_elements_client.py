from mtx_api.client._mtx_http_client import Method, MtxHttpClient
from mtx_api.models.errors import MissingJurisdictionCodesError
from mtx_api.models.jurisdiction import JurisdictionElementList


class JurisdictionElementsClient:
    def __init__(self, client: MtxHttpClient):
        self._client: MtxHttpClient = client

    async def list(
        self,
        *,
        access_token: str | None = None,
        jurisdiction_code: str,
    ) -> JurisdictionElementList:
        """Retrieves jurisdiction elements associated with a specific jurisdiction code.

        Use this tool to find all jurisdiction elements linked to a given jurisdiction code
        from the platform.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.
            jurisdiction_code: The unique string code of the jurisdiction to query.

        Returns:
            JurisdictionElementList: An object containing the list of retrieved
                jurisdiction elements.

        Raises:
            MissingJurisdictionCodesError: If the `jurisdiction_code` argument is missing or empty.
        """
        if not jurisdiction_code:
            raise MissingJurisdictionCodesError()

        return await self._client.http_request(
            method=Method.GET,
            path=f"jurisdiction/{jurisdiction_code}/jurisdiction-elements",
            model=JurisdictionElementList,
            access_token=access_token,
        )
