from __future__ import annotations

from collections.abc import Sequence

from mtx_api.client._mtx_http_client import (
    Method,
    MtxHttpClient,
    array_query_param,
)
from mtx_api.models.additional_data import AdditionalDataValue
from mtx_api.models.errors import (
    MissingArgumentError,
    MissingJurisdictionCodesError,
    MissingRequestIdError,
    MissingServiceIdError,
)
from mtx_api.models.request import (
    CreatedRequest,
    CreatedRequestList,
    Request,
    RequestList,
)
from mtx_api.models.request_comment import RequestComment
from mtx_api.models.request_media import RequestMedia


class RequestClient:
    def __init__(self, client: MtxHttpClient):
        self._client: MtxHttpClient = client

    async def create(
        self,
        *,
        access_token: str | None = None,
        service_id: str,
        jurisdiction_code: str,
        jurisdiction_element_id: str | None = None,
        origin_device_id: str | None = None,
        description: str | None = None,
        public: bool | None = None,
        lat: float | None = None,
        lng: float | None = None,
        address_string: str | None = None,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        twitter_nickname: str | None = None,
        additional_data: Sequence[AdditionalDataValue] | None = None,
    ) -> CreatedRequest:
        """Create a new request in the platform.

        This function allows creating a new request (issue report) within a specific jurisdiction.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.
            service_id: Identifier of the service to request.
            jurisdiction_code: Code of the jurisdiction where the request is made.
            jurisdiction_element_id: Optional ID of a specific element within the jurisdiction.
            origin_device_id: Optional ID of the device making the request.
                Can be found on Jurisdiction detail.
            description: Optional textual description of the request.
            public: Optional boolean. If True, the request is public; if False, it is private.
            lat: Optional latitude coordinate of the request location.
            lng: Optional longitude coordinate of the request location.
            address_string: Optional physical address associated with the request.
            email: Optional email address of the person making the request.
            first_name: Optional first name of the person making the request.
            last_name: Optional last name of the person making the request.
            phone: Optional phone number of the person making the request.
            twitter_nickname: Optional Twitter handle of the person making the request.
            additional_data: Optional sequence of additional data values required by the service.

        Returns:
            CreatedRequest: The created request instance with its details.

        Raises:
            MissingJurisdictionCodesError: If jurisdiction_code is missing.
            MissingServiceIdError: If service_id is missing.
        """
        if not jurisdiction_code:
            raise MissingJurisdictionCodesError()

        if not service_id:
            raise MissingServiceIdError()

        body: dict[str, object] = {
            "service_id": service_id,
            "jurisdiction_id": jurisdiction_code,
            "description": description,
            "address_string": address_string,
            "jurisdiction_element": jurisdiction_element_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "twitter_nickname": twitter_nickname,
            "device_type": origin_device_id,
            "additionalData": (
                [ad.model_dump(by_alias=True) for ad in additional_data]
                if additional_data
                else None
            ),
        }
        if lat is not None and lng is not None:
            body["lat"] = lat
            body["long"] = lng
        if public is not None:
            body["public"] = "true" if public else "false"

        response = await self._client.http_request(
            method=Method.POST,
            path="requests",
            model=CreatedRequestList,
            access_token=access_token,
            body=body,
        )
        return response.root[0]

    async def list(
        self,
        *,
        access_token: str | None = None,
        jurisdiction_codes: list[str] | None = None,
        service_request_ids: list[str] | None = None,
        service_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        own: bool | None = None,
        lat: float | None = None,
        lng: float | None = None,
        page: int | None = None,
        limit: int | None = None,
        address_and_service_request_id: str | None = None,
        status: list[str] | None = None,
        typology_ids: list[str] | None = None,
        distance: int | None = None,
        following: bool | None = None,
        order: str | None = None,
        complaints: bool | None = None,
        reiterations: bool | None = None,
        user_reiterated: bool | None = None,
        user_complaint: bool | None = None,
        jurisdiction_element_ids: list[str] | None = None,
        level: int | None = None,
        polygon: list[float] | None = None,
        final_ok: bool | None = None,
        final_not_ok: bool | None = None,
        final_status: bool | None = None,
        interested: bool | None = None,
        timezone: str | None = None,
    ) -> RequestList:
        """List and filter requests from the platform.

        This function retrieves a list of requests based on multiple filtering criteria.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.
            jurisdiction_codes: Optional list of jurisdiction codes to filter by.
            service_request_ids: Optional list of specific request IDs to retrieve.
            service_ids: Optional list of service IDs to filter by.
            start_date: Optional ISO date-time string (inclusive) to filter requests created
                after this date.
            end_date: Optional ISO date-time string (inclusive) to filter requests created
                before this date.
            own: Optional boolean. If True, returns only requests created by the authenticated user.
            lat: Optional latitude to be used for distance filtering or ordering by proximity.
            lng: Optional longitude to be used for distance filtering or ordering by proximity.
            page: Optional page number for pagination.
            limit: Optional number of items per page.
            address_and_service_request_id: Optional free text search for address or
                service request ID.
            status: Optional list of status codes to filter by.
            typology_ids: Optional list of typology IDs to filter by.
            distance: Optional radius in meters to filter requests around the provided lat/lng.
            following: Optional boolean. If True, returns only requests followed by the
                authenticated user.
            order: Optional ordering strategy (e.g., "newest_date_desc").
            complaints: Optional boolean. If True, filters only complaints.
            reiterations: Optional boolean. If True, filters only reiterations.
            user_reiterated: Optional boolean. If True, filters requests reiterated by
                the authenticated user.
            user_complaint: Optional boolean. If True, filters complaints made by the
                authenticated user.
            jurisdiction_element_ids: Optional list of jurisdiction element IDs to filter by.
            level: Optional floor level to filter by.
            polygon: Optional list of float coordinates describing a polygon area to filter requests
                within.
            final_ok: Optional boolean. If True, filters requests with a final status of OK.
            final_not_ok: Optional boolean. If True, filters requests with a final status of NOT OK.
            final_status: Optional boolean. If True, filters requests with any final status.
            interested: Optional boolean. If True, filters requests where the user has expressed
                interest.
            timezone: Optional IANA timezone string used by the backend for date filtering.

        Returns:
            RequestList: A list of Request items matching the criteria.
        """

        params = {
            "start_date": start_date,
            "end_date": end_date,
            "own": own,
            "page": page,
            "limit": limit,
            "address_and_service_request_id": address_and_service_request_id,
            "distance": distance,
            "following": following,
            "order": order,
            "complaints": complaints,
            "reiterations": reiterations,
            "user_reiterated": user_reiterated,
            "user_complaint": user_complaint,
            "level": level,
            "final_ok": final_ok,
            "final_not_ok": final_not_ok,
            "final_status": final_status,
            "interested": interested,
            "timezone": timezone,
            "lat": lat,
            "long": lng,
            **array_query_param("jurisdiction_ids", jurisdiction_codes),
            **array_query_param("service_request_ids", service_request_ids),
            **array_query_param("service_ids", service_ids),
            **array_query_param("status", status),
            **array_query_param("typologies", typology_ids),
            **array_query_param("jurisdiction_element_ids", jurisdiction_element_ids),
            **array_query_param("polygon", polygon),
        }

        return await self._client.http_request(
            method=Method.GET,
            path="requests",
            model=RequestList,
            access_token=access_token,
            query_params=params,
        )

    async def detail(
        self,
        *,
        access_token: str | None = None,
        request_id: str,
    ) -> Request:
        """Retrieve detailed information about a specific request.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.
            request_id: The unique identifier of the request to fetch.
                Note: this is the internal request `id`, not the `service_request_id`.

        Returns:
            Request: The detailed Request object containing all information.

        Raises:
            MissingRequestIdError: If request_id is missing.
        """
        if not request_id:
            raise MissingRequestIdError()
        return await self._client.http_request(
            method=Method.GET,
            path=f"requests/{request_id}",
            model=Request,
            access_token=access_token,
        )

    async def attach_media(
        self,
        *,
        access_token: str | None = None,
        request_id: str,
        jurisdiction_code: str,
        file: tuple[str, bytes],
    ) -> RequestMedia:
        """Attach a media file to an existing request.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.
            request_id: The identifier of the request to which the media will be attached.
                Note: this is the internal request `id`, not the `service_request_id`.
            jurisdiction_code: The code of the jurisdiction associated with the request.
            file: A tuple containing the file name (str) and the file content (bytes).

        Returns:
            RequestMedia: The object representing the attached media.

        Raises:
            MissingRequestIdError: If request_id is missing.
            MissingJurisdictionCodesError: If jurisdiction_code is missing.
            MissingArgumentError: If file content or file name is empty, or if extension is missing.
        """
        if not request_id:
            raise MissingRequestIdError()
        if not jurisdiction_code:
            raise MissingJurisdictionCodesError()
        (file_name, file_content) = file
        if not file_content:
            raise MissingArgumentError("file content must not be empty")
        if not file_name:
            raise MissingArgumentError("file name must not be empty")
        if "." not in file_name:
            raise MissingArgumentError("file_name has no extension.")

        return await self._client.http_request(
            method=Method.POST,
            path="requests_medias",
            model=RequestMedia,
            access_token=access_token,
            query_params={
                "jurisdiction_id": jurisdiction_code,
            },
            body={
                "token": request_id,
            },
            files={
                "media": file,
            },
        )

    async def attach_comment(
        self,
        *,
        access_token: str | None = None,
        request_id: str,
        comment: str | None = None,
        files: Sequence[tuple[str, bytes]] = (),
    ) -> RequestComment:
        """Attach a comment to an existing request.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.
            request_id: The identifier of the request to which the comment will be added.
                Note: this is the internal request `id`, not the `service_request_id`.
            comment: Optional text of the comment. Can be empty.
            files: Optional sequence of files to attach with the comment.
                Each file is a tuple containing the file name (str) and the file content (bytes).

        Returns:
            RequestComment: The created comment object.

        Raises:
            MissingRequestIdError: If request_id is missing.
        """
        if not request_id:
            raise MissingRequestIdError()

        return await self._client.http_request(
            method=Method.POST,
            path="requests_comments",
            model=RequestComment,
            access_token=access_token,
            body={
                k: v
                for k, v in {
                    "token": request_id,
                    "description": comment,
                }.items()
                if v is not None
            },
            files=(
                {
                    f"medias_data[{i}]": (file_name, file_content)
                    for i, (file_name, file_content) in enumerate(files)
                    if file_name and file_content and "." in file_name
                }
                if files
                else None
            ),
        )
