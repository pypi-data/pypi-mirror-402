from pydantic import AliasChoices, Field, RootModel

from mtx_api.models.base import ImmutableBaseModel


class OriginDevice(ImmutableBaseModel):
    """
    Represents the type of origin device associated with a jurisdiction.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the origin device.",
        min_length=1,
    )
    options: list[str] | None = Field(
        default=None,
        description="List of configuration options available for the device."
        "Can be one of 'android', 'email', 'facebook', 'inperson', 'internal', 'ios', "
        "'twitter', 'web_channel', 'bot_whatsapp', 'bot_telegram', 'bot_web',",
    )


class JurisdictionElement(ImmutableBaseModel):
    """
    Represents a specific component or administrative division within a jurisdiction.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the jurisdiction element.",
        min_length=1,
    )
    name: str | None = Field(
        default=None,
        description="Name of the jurisdiction element.",
        min_length=1,
    )
    type: str | None = Field(
        default=None,
        description="Type classification of the element. It can be 'city' or 'building'",
        min_length=1,
    )
    visible_name: str | None = Field(
        default=None,
        description="Human-readable name.",
        min_length=1,
    )
    is_main: bool | None = Field(
        default=None,
        description="Indicates whether this is the primary element for the jurisdiction.",
    )


class Jurisdiction(ImmutableBaseModel):
    """
    Represents a geographical or administrative jurisdiction entity
    within the platform, usually a city.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the jurisdiction.",
        min_length=1,
    )
    name: str | None = Field(
        default=None,
        description="Official name of the jurisdiction.",
        min_length=1,
    )
    jurisdiction_code: str | None = Field(
        default=None,
        validation_alias=AliasChoices("jurisdiction_id", "jurisdiction_code"),
        serialization_alias="jurisdiction_id",
        description="Code identifying the jurisdiction within the platform",
        min_length=1,
    )
    jurisdiction_elements: list[JurisdictionElement] | None = Field(
        default=None,
        description="Administrative elements that belong to this jurisdiction.",
    )
    origin_devices: list[OriginDevice] | None = Field(
        default=None,
        description="List of devices associated with this jurisdiction.",
    )


class JurisdictionElementList(RootModel[list[JurisdictionElement]]):
    """
    A collection of JurisdictionElement objects.
    """

    pass


class JurisdictionList(RootModel[list[Jurisdiction]]):
    """
    A collection of Jurisdiction objects.
    """

    pass
