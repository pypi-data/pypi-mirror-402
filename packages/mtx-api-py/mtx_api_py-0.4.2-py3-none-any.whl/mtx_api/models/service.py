from pydantic import AliasChoices, Field, RootModel

from mtx_api.models.additional_data import AdditionalData
from mtx_api.models.base import ImmutableBaseModel
from mtx_api.models.typology import Typology


class MandatoryInformantField(ImmutableBaseModel):
    """
    Represents a required field configuration for informant information.
    This model defines which fields must be provided by the person reporting
    a request, along with validation messages.
    """

    field: str | None = Field(
        default=None,
        description="The name of the field that is required (e.g., 'first_name', 'email').",
    )
    message: str | None = Field(
        default=None,
        description="The validation message if the field is missing or invalid.",
    )
    required: bool | None = Field(
        default=None,
        description="Whether this field is mandatory for submission.",
    )


class StatusNode(ImmutableBaseModel):
    """
    Represents a status node in the request lifecycle workflow.

    Status nodes define the different stages a request can be in,
    such as 'new', 'in progress', 'resolved', etc. They form a workflow
    that tracks request progression.
    """

    status_node_type: str | None = Field(
        default=None,
        description="The type of status node (e.g., 'initial_node', 'intermediate_node', 'final_node').",
    )
    name: str | None = Field(
        default=None,
        description="Internal name of the status node.",
    )
    typology_node_id: str | None = Field(
        default=None,
        description="Identifier linking this status node to a typology node.",
    )
    visible_name: str | None = Field(
        default=None,
        description="Human-readable name given to users for this status.",
    )
    id: str | None = Field(
        default=None,
        description="Unique identifier for the status node.",
    )
    order: int | None = Field(
        default=None,
        description="The showing order of this status in the workflow sequence.",
    )
    planned: bool | None = Field(
        default=None,
        description="Whether this status represents a planned or scheduled state.",
    )


class Service(ImmutableBaseModel):
    """
    Represents a service category for citizen reports.

    A Service defines a specific category of issues or requests that citizens
    can report to a jurisdiction. It configures what information is required from reporters,
    upload requirements, visibility settings, the workflow status progression, etc.
    """

    id: str | None = Field(
        default=None,
        description="Unique identifier for the service.",
    )
    visible_name: str | None = Field(
        default=None,
        description="Human-readable name given to users.",
    )
    service_name: str | None = Field(
        default=None,
        description="Internal name of the service.",
    )
    description: str | None = Field(
        default=None,
        description="Detailed description of what the service provides.",
    )
    parent_service_name: str | None = Field(
        default=None,
        description="Name of the parent service if this is a sub-service.",
    )
    jurisdiction_code: str | None = Field(
        default=None,
        validation_alias=AliasChoices("jurisdiction_id", "jurisdiction_code"),
        serialization_alias="jurisdiction_id",
        description="Code of the jurisdiction where this service is available.",
    )
    typology: Typology | None = Field(
        default=None,
        description="The typology classification associated with this service.",
    )
    keywords: str | None = Field(
        default=None,
        description="Comma-separated keywords for searching and categorizing the service.",
    )
    mandatory_description: bool | None = Field(
        default=None,
        description="Whether a text description is required when submitting a request for this service.",
    )
    mandatory_files: bool | None = Field(
        default=None,
        description="Whether file uploads are required when submitting a request for this service.",
    )
    mandatory_medias: bool | None = Field(
        default=None,
        description="Whether media uploads (images/videos) are required when submitting a request.",
    )
    max_upload_files: int | None = Field(
        default=None,
        description="Maximum number of files that can be uploaded with a request.",
    )
    max_upload_medias: int | None = Field(
        default=None,
        description="Maximum number of media items that can be uploaded with a request.",
    )
    public: bool | None = Field(
        default=None,
        description="Whether this service is publicly visible and available to all users.",
    )
    public_requests: bool | None = Field(
        default=None,
        description="Whether requests made for this service are publicly visible.",
    )
    deleted: bool | None = Field(
        default=None,
        description="Whether this service has been marked as deleted.",
    )
    social: bool | None = Field(
        default=None,
        description="Whether this service has social features enabled.",
    )
    evaluation: bool | None = Field(
        default=None,
        description="Whether users can evaluate or rate this service.",
    )
    hide_estimated_date: bool | None = Field(
        default=None,
        alias="hideEstimatedDate",
        description="Whether to hide the estimated completion date from users.",
    )
    additional_data: AdditionalData | None = Field(
        default=None,
        alias="additionalData",
        description="Additional configurable questions and data fields for this service.",
    )
    mandatory_informant_config: list[MandatoryInformantField] | None = Field(
        default=None,
        description="Configuration defining which informant fields are required.",
    )
    public_requests_internal: bool | None = Field(
        default=None,
        description="Whether requests are visible internally to authorized users.",
    )
    allow_changing_request_privacy: bool | None = Field(
        default=None,
        description="Whether users can change the privacy settings of their requests.",
    )
    service_code: str | None = Field(
        default=None,
        description="A unique code identifier for the service.",
    )
    status_node: list[StatusNode] | None = Field(
        default=None,
        description="List of status nodes defining the request lifecycle workflow.",
    )
    with_informant: bool | None = Field(
        default=None,
        description="Whether this service requires informant details.",
    )
    with_internal_informant: bool | None = Field(
        default=None,
        description="Whether this service supports internal informant submissions.",
    )
    with_authorized_internal_users: bool | None = Field(
        default=None,
        description="Whether authorized internal users can access this service.",
    )


class ServiceList(RootModel[list[Service]]):
    """
    A collection of Service objects.

    This model represents a list of services returned when querying
    available services for a jurisdiction.
    """

    pass
