from __future__ import annotations

from pydantic import AliasChoices, Field

from mtx_api.models.base import DatetimeField, ImmutableBaseModel


class RequestCommentMedia(ImmutableBaseModel):
    """
    Represents media content attached to a request comment.

    This model contains information about images, videos, or other media files
    that have been attached to a comment on a request.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the comment media item.",
    )
    media_url: str | None = Field(
        default=None,
        description="The URL where the media content can be accessed.",
    )


class RequestComment(ImmutableBaseModel):
    """
    Represents a comment or note attached to a request.

    This model contains user-submitted comments on requests, which can
    include text descriptions and attached media files for additional context.
    """

    created_datetime: DatetimeField | None = Field(
        default=None,
        description="The timestamp when the comment was created, in ISO format with timezone.",
    )
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("comment_code", "id"),
        serialization_alias="comment_code",
        description="Unique identifier for the comment.",
    )
    description: str | None = Field(
        default=None,
        description="The text content of the comment.",
    )
    medias: list[RequestCommentMedia] | None = Field(
        default=None,
        validation_alias=AliasChoices("medias_urls", "medias"),
        serialization_alias="medias_urls",
        description="List of media items attached to the comment.",
    )
