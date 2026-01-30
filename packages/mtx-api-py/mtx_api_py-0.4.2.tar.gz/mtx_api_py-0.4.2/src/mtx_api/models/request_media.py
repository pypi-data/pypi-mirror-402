from __future__ import annotations

from pydantic import Field

from mtx_api.models.base import DatetimeField, ImmutableBaseModel


class RequestMedia(ImmutableBaseModel):
    """
    Represents media content attached to a request.

    This model contains information about images, videos, or other media files
    that have been uploaded and associated with a request for
    documentation or evidence purposes.
    """

    type: str | None = Field(
        default=None,
        description="The media type, such as 'image', 'video', or other content types.",
    )
    media_url: str | None = Field(
        default=None,
        description="The URL where the media content can be accessed.",
    )
    created_datetime: DatetimeField | None = Field(
        default=None,
        description="The timestamp when the media was uploaded, in ISO format with timezone.",
    )
    media_code: str | None = Field(
        default=None,
        description="A unique code or reference identifier for the media item.",
    )
