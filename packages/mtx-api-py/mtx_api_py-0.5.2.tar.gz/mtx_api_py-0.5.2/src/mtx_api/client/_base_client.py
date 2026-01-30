from __future__ import annotations

from mtx_api.client._mtx_http_client import Method, MtxHttpClient
from mtx_api.models.base import EmptyResponse, TextResponse


class BaseClient:
    def __init__(self, client: MtxHttpClient):
        self._client: MtxHttpClient = client

    async def status(
        self,
        *,
        access_token: str | None = None,
    ) -> bool:
        """Checks the operational status of the platform.

        Verifies if the platform is running and reachable. Use this tool
        to confirm platform availability before performing other operations.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.

        Returns:
            bool: True if the platform is available and the operation succeeds.
        """
        await self._client.http_request(
            method=Method.GET,
            path="",
            model=EmptyResponse,
            access_token=access_token,
        )
        return True

    async def openapi(self) -> str:
        """Retrieves the OpenAPI specification of the platform.

        Fetches the complete OpenAPI documentation in plain text. This provides details on available
        tools, operation structures, and expected responses.

        Returns:
            str: The OpenAPI document content as a string.
        """
        resp = await self._client.http_request(
            method=Method.GET,
            path="openapi",
            model=TextResponse,
        )
        return resp.text
