from typing import Literal

from pydantic import AliasChoices, Field

from mtx_api.models.base import ImmutableBaseModel


class Authentication(ImmutableBaseModel):
    """
    Represents authentication credentials for a user session.

    This model contains the tokens required to authenticate operations on the platform.
    The access token is used for authorized operations, while the refresh token allows
    obtaining a new access token when it expires.
    """

    access_token: str = Field(
        description="The bearer token used to authenticate operations on the platform.",
    )
    refresh_token: str = Field(
        description="The token used to obtain a new access token when the current one expires.",
    )
    expires_in: int = Field(
        description="The number of seconds until the access token expires.",
    )
    token_type: str = Field(
        description="The type of token, typically 'bearer' for OAuth2 tokens.",
    )


type Gender = Literal["male", "female", "other", "not_specified"]


class Profile(ImmutableBaseModel):
    """
    Represents a user profile with personal information and account details.

    This model contains all the personal and account information associated with
    a user on the platform. It includes identification, contact information,
    and demographic data.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the user profile.",
    )
    email: str | None = Field(
        default=None,
        description="The user's email address used for contact and authentication.",
    )
    username: str | None = Field(
        default=None,
        description="The user's chosen username, typically their email address.",
    )
    first_name: str | None = Field(
        default=None,
        description="The user's first name or given name.",
    )
    last_name: str | None = Field(
        default=None,
        description="The user's last name or family name.",
    )
    twitter_nickname: str | None = Field(
        default=None,
        validation_alias=AliasChoices("twitter_nickname", "twitterNickname"),
        serialization_alias="twitterNickname",
        description="The user's Twitter handle or social media nickname visible to others.",
    )
    anonymous: bool | None = Field(
        default=None,
        description="Whether the user is logged in anonymously without a registered account.",
    )
    phone: str | None = Field(
        default=None,
        description="The user's primary phone number for contact purposes.",
    )
    gender: Gender | None = Field(
        default=None,
        description="The user's gender identification.",
    )
    birthday: str | None = Field(
        default=None,
        description="The user's date of birth in format YYYY-MM-DD.",
    )
