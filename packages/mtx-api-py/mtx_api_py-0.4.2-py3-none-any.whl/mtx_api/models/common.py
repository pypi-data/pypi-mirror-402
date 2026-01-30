from __future__ import annotations

from pydantic import Field

from mtx_api.models.base import ImmutableBaseModel


class Tag(ImmutableBaseModel):
    """
    Represents a label or category tag for classification purposes.

    Tags are used throughout the platform to categorize and filter various
    entities such as questions, services, or other content items.
    """

    name: str | None = Field(
        default=None,
        description="The name of the tag.",
    )
    id: str | None = Field(
        default=None,
        description="Unique identifier for the tag.",
    )


class User(ImmutableBaseModel):
    """
    Represents a basic user reference with minimal information.

    This simplified model is used when referencing a user in contexts where
    only the identifier is needed, without full profile details.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the user.",
    )


class Location(ImmutableBaseModel):
    """
    Represents geographic coordinates for a location on Earth.

    This model uses the standard GPS coordinates system
    with latitude and longitude.
    """

    lat: float | None = Field(
        default=None,
        description="Latitude coordinate.",
    )
    lng: float | None = Field(
        default=None,
        description="Longitude coordinate.",
    )


class LegalText(ImmutableBaseModel):
    """
    Represents the legal documentation content required for platform usage.

    This model encapsulates all legal text content that users must review and
    accept to use the platform. Each field may contain plain text, formatted
    text, or links to external legal documents.
    """

    privacy_policy: str | None = Field(
        default=None,
        description=(
            "The privacy policy content describing how user data is collected, "
            "processed, and protected. May be plain text or a link to the full document."
        ),
    )
    terms_of_use: str | None = Field(
        default=None,
        description=(
            "The terms of use content outlining the rules and conditions for using "
            "the platform. May be plain text or a link to the full document."
        ),
    )
    cookies_policy: str | None = Field(
        default=None,
        description=(
            "The cookies policy content explaining how cookies are used on the platform. "
            "May be plain text or a link to the full document."
        ),
    )


class LegalTerms(ImmutableBaseModel):
    """
    Container model for platform legal terms and conditions.

    This model serves as a wrapper for all legal documentation that users must
    accept before using the platform. It is typically retrieved when showing
    legal information during registration or when terms have been updated.
    """

    legal_text: LegalText | None = Field(
        default=None,
        description="The complete legal documentation including privacy policy, terms of use, and cookies policy.",
    )
