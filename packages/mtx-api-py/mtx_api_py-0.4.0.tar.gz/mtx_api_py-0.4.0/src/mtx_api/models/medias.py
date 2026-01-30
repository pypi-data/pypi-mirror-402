from __future__ import annotations

from pydantic import Field

from mtx_api.models.additional_data import AdditionalDataAnswer
from mtx_api.models.base import ImmutableBaseModel
from mtx_api.models.common import Tag


class MediaMetadata(ImmutableBaseModel):
    """
    Represents metadata information associated with media files.

    This model contains additional contextual data about media, including
    location-based information and creation timestamps.
    """

    location_additional_data: list[AdditionalDataAnswer] | None = Field(
        default=None,
        description="Additional location-based data associated with where the media was captured.",
    )
    created: str | None = Field(
        default=None,
        description="The timestamp when the media metadata was created, in ISO format.",
    )


class File(ImmutableBaseModel):
    """
    Represents a file resource with its identifier and access URL.

    This model provides basic file information for accessing uploaded or
    stored files on the platform.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the file.",
    )
    url: str | None = Field(
        default=None,
        description="The URL where the file can be accessed or downloaded.",
    )


class Media(ImmutableBaseModel):
    """
    Represents media content such as images or videos attached to platform entities.

    This model contains comprehensive information about media files including
    their visibility, type, metadata, and validation checks.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the media item.",
    )
    public: bool | None = Field(
        default=None,
        description="Whether the media is publicly visible or restricted to authorized users.",
    )
    type: str | None = Field(
        default=None,
        description="The media type, such as 'image', 'video', or other content types.",
    )
    media_url: str | None = Field(
        default=None,
        description="The URL where the media content can be accessed.",
    )
    created_datetime: str | None = Field(
        default=None,
        description="The timestamp when the media was created or uploaded, in ISO format.",
    )
    deleted: bool | None = Field(
        default=None,
        description="Whether the media has been marked as deleted.",
    )
    media_code: str | None = Field(
        default=None,
        description="A code or reference identifier for the media item.",
    )
    check_distance: str | None = Field(
        default=None,
        description="Distance-based validation check value for media verification.",
    )
    check_time: str | None = Field(
        default=None,
        description="Time-based validation check value for media verification.",
    )
    media_metadata: MediaMetadata | None = Field(
        default=None,
        description="Additional metadata information associated with the media.",
    )
    tags: list[Tag] | None = Field(
        default=None,
        description="Classification tags associated with the media for categorization.",
    )
