from pydantic import Field, RootModel

from mtx_api.models.base import ImmutableBaseModel


class Typology(ImmutableBaseModel):
    """
    Represents a classification or category for a service within the platform.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the typology.",
    )
    name: str | None = Field(
        default=None,
        description="Internal system name for the typology.",
    )
    visible_name: str | None = Field(
        default=None,
        description="Human-readable name of the typology given to the user.",
    )
    description_legend: str | None = Field(
        default=None,
        description="Short descriptive legend associated with the typology, "
        "used to prompt the user when creating a request",
    )
    typology_description: str | None = Field(
        default=None,
        description="Describes the intent of the user when creating a request of this typology.",
    )
    order: int | None = Field(
        default=None,
        description="Numeric value used to determine the sorting order of the typology in lists.",
    )
    public: bool | None = Field(
        default=None,
        description="Flag indicating whether this typology is publicly accessible.",
    )
    has_location: bool | None = Field(
        default=None,
        alias="hasLocation",
        description="Flag indicating if this typology requires or supports location data.",
    )
    location_type: str | None = Field(
        default=None,
        description="Specifies the type of location associated with this typology, if applicable."
        "It can be one of: 'geolocation', 'indoor' or 'none'.",
    )
    with_description: bool | None = Field(
        default=None,
        description="Flag indicating if a description input is enabled when creating requests.",
    )
    with_files: bool | None = Field(
        default=None,
        description="Flag indicating if file attachments are supported for this typology.",
    )
    with_medias: bool | None = Field(
        default=None,
        description="Flag indicating if media (images/videos) support is enabled.",
    )


class TypologyList(RootModel[list[Typology]]):
    """
    A collection of Typology objects.
    """

    pass
