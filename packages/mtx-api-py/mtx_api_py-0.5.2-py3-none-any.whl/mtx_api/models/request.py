from __future__ import annotations

from pydantic import AliasChoices, Field, RootModel

from mtx_api.models.additional_data import AdditionalDataAnswer
from mtx_api.models.base import DatetimeField, ImmutableBaseModel
from mtx_api.models.common import Tag, User
from mtx_api.models.jurisdiction import JurisdictionElement
from mtx_api.models.medias import File, Media
from mtx_api.models.service import StatusNode
from mtx_api.models.typology import Typology


class Following(ImmutableBaseModel):
    """
    Represents whether a user is following a request.

    This model indicates if the current user has subscribed to receive
    notifications about updates to a particular request.
    """

    is_following: bool | None = Field(
        default=None,
        alias="isFollowing",
        description="Whether the current user is following this request.",
    )


class CreatedRequest(ImmutableBaseModel):
    """
    Represents a newly created request with basic information.

    This model contains the essential identifiers and status information
    returned immediately after creating a request.
    """

    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("token", "id"),
        serialization_alias="token",
        description="Unique identifier token for the created request.",
    )
    service_request_id: str | None = Field(
        default=None,
        description="Human-readable identifier for the request.",
    )
    status_node: StatusNode | None = Field(
        default=None,
        description="The initial status node of the newly created request.",
    )


class CreatedRequestList(RootModel[list[CreatedRequest]]):
    pass


class Request(CreatedRequest):
    """
    Represents a complete request with all its details and metadata.

    This model extends CreatedRequest with comprehensive information including
    location data, timestamps, status, media attachments, user interactions,
    and additional configurable fields.
    """

    description: str | None = Field(
        default=None,
        description="The detailed description of the request provided by the user.",
    )
    address: str | None = Field(
        default=None,
        description="The physical address associated with the request.",
    )
    address_string: str | None = Field(
        default=None,
        description="Alternative formatted address string for the request location.",
    )
    lat: float | None = Field(
        default=None,
        description="Latitude coordinate of the request location.",
    )
    lng: float | None = Field(
        default=None,
        alias="long",
        description="Longitude coordinate of the request location.",
    )
    status_node_type: str | None = Field(
        default=None,
        description="The type of the current status node (e.g., 'initial_node', 'final_node').",
    )
    typology: Typology | None = Field(
        default=None,
        description="The typology classification of the request.",
    )
    jurisdiction_id: str | None = Field(
        default=None,
        description="Code of the jurisdiction where the request was created.",
    )
    jurisdiction_element: JurisdictionElement | None = Field(
        default=None,
        description="The specific jurisdiction element associated with the request.",
    )
    service_id: str | None = Field(
        default=None,
        description="Unique identifier of the service this request belongs to.",
    )
    service_name: str | None = Field(
        default=None,
        description="Internal name of the service.",
    )
    service_code: str | None = Field(
        default=None,
        description="Code identifier of the service.",
    )
    requested_datetime: DatetimeField | None = Field(
        default=None,
        description="Timestamp when the request was created, in ISO format with timezone.",
    )
    updated_datetime: DatetimeField | None = Field(
        default=None,
        description="Timestamp when the request was last updated, in ISO format with timezone.",
    )
    current_node_estimated_final_datetime: DatetimeField | None = Field(
        default=None,
        description="Estimated completion time for the current status node, in ISO format with timezone.",
    )
    current_node_estimated_start_datetime: DatetimeField | None = Field(
        default=None,
        description="Estimated start time for the current status node, in ISO format with timezone.",
    )
    estimated_final_datetime: DatetimeField | None = Field(
        default=None,
        description="Estimated completion time for the entire request, in ISO format with timezone.",
    )
    estimated_start_datetime: DatetimeField | None = Field(
        default=None,
        description="Estimated start time for processing the request, in ISO format with timezone.",
    )
    reiterations_count: int | None = Field(
        default=None,
        description="Number of times the request has been reiterated by users.",
    )
    complaints_count: int | None = Field(
        default=None,
        description="Number of complaints filed about this request.",
    )
    comments_count: int | None = Field(
        default=None,
        description="Number of comments posted on this request.",
    )
    worknotes_count: int | None = Field(
        default=None,
        description="Number of internal work notes on this request.",
    )
    evaluation: int | None = Field(
        default=None,
        description="User's evaluation rating for this request.",
    )
    evaluations_count: int | None = Field(
        default=None,
        description="Total number of evaluations received for this request.",
    )
    evaluations_avg: int | None = Field(
        default=None,
        description="Average evaluation rating across all evaluations.",
    )
    public_visibility: bool | None = Field(
        default=None,
        description="Whether this request is visible to the public.",
    )
    complaining: bool | None = Field(
        default=None,
        description="Whether the current user has filed a complaint about this request.",
    )
    supporting: bool | None = Field(
        default=None,
        description="Whether the current user is supporting this request.",
    )
    supporting_count: int | None = Field(
        default=None,
        description="Number of users supporting this request.",
    )
    following_count: int | None = Field(
        default=None,
        description="Number of users following this request.",
    )
    following: Following | None = Field(
        default=None,
        description="Information about whether the current user is following this request.",
    )
    deleted: bool | None = Field(
        default=None,
        description="Whether this request has been marked as deleted.",
    )
    jurisdiction_name: str | None = Field(
        default=None,
        description="Name of the jurisdiction where the request was created.",
    )
    is_evaluable: bool | None = Field(
        default=None,
        description="Whether this request can be evaluated by the user.",
    )
    accepted: bool | None = Field(
        default=None,
        description="Whether this request has been accepted for processing.",
    )
    files: list[File] | None = Field(
        default=None,
        description="List of file attachments associated with this request.",
    )
    medias: list[Media] | None = Field(
        default=None,
        description="List of media items (images/videos) attached to this request.",
    )
    tags: list[Tag] | None = Field(
        default=None,
        description="Classification tags associated with this request.",
    )
    media_url: str | None = Field(
        default=None,
        description="URL to a primary media item for this request.",
    )
    additional_data: list[AdditionalDataAnswer] | None = Field(
        default=None,
        description="Answers to additional configurable questions for this request.",
    )
    location_additional_data: list[AdditionalDataAnswer] | None = Field(
        default=None,
        description="Location-specific additional data answers for this request.",
    )
    user: User | None = Field(
        default=None,
        description="Reference to the user who created this request.",
    )


class RequestList(RootModel[list[Request]]):
    """
    A collection of Request objects.

    This model represents a list of requests returned when querying
    multiple requests from the platform.
    """

    pass
