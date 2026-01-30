from abc import ABC
from collections.abc import Sequence
from typing import Any

from pydantic import AliasChoices, Field, RootModel, field_serializer

from mtx_api.models.base import DatetimeField, ImmutableBaseModel
from mtx_api.models.common import Location, Tag


class Question(ImmutableBaseModel):
    """
    Represents a configurable question that can be asked when creating a request.

    Questions are used to gather additional information from users during the request
    creation process. They can have different types (label, text, number, etc.) and may include
    predefined possible answers.
    """

    type: str | None = Field(
        default=None,
        description="The type of question input (label, number, boolean, color, datetime, "
        "position, singleValueList, multiValueList, url, signature, image, "
        "imageGallery, audioClip or videoClip).",
    )
    active: bool | None = Field(
        default=None,
        description="Whether this question is currently active and should be used.",
    )
    code: str | None = Field(
        default=None,
        description="Unique code identifier for the question.",
    )
    help_text: str | None = Field(
        default=None,
        description="Additional help text or instructions given to the user.",
    )
    id: str | None = Field(
        default=None,
        description="Unique identifier for the question.",
    )
    question: str | None = Field(
        default=None,
        description="The question text given to the user.",
    )
    tags: list[Tag] | None = Field(
        default=None,
        description="Classification tags associated with this question.",
    )
    possible_answers: list["PossibleAnswer"] | None = Field(
        default=None,
        description="List of predefined answer options for singleValueList or multiValueList type questions.",
    )


class ConfigurableQuestion(ImmutableBaseModel):
    """
    Represents a question with its configuration settings.

    This model extends a base question with additional metadata that controls
    how and when the question is given in different contexts (forms, details...).
    """

    editable: bool | None = Field(
        default=None,
        description="Whether the answer to this question can be edited after initial submission.",
    )
    omit_in_detail: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("omit_in_detail", "hidden_in_open010_detail"),
        serialization_alias="hidden_in_open010_detail",
        description=(
            "Whether this question should be hidden when the request details. "
            "When True, the question and its answer will not appear in the detail of a request."
        ),
    )
    omit_in_form: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("omit_in_form", "hidden_in_open010_form"),
        serialization_alias="hidden_in_open010_form",
        description=(
            "Whether this question should be hidden in the request. "
            "When True, the question will not be given to users when creating a new request."
        ),
    )
    question: Question | None = Field(
        default=None,
        description="The underlying question definition with its content and options.",
    )
    required: bool | None = Field(
        default=None,
        description="Whether an answer to this question is mandatory for submission.",
    )
    default_value: str | None = Field(
        default=None,
        description="The default value pre-filled for this question.",
    )
    response_attribute: str | None = Field(
        default=None,
        description="The attribute name where the response should be stored.",
    )


class AdditionalData(ImmutableBaseModel):
    """
    Represents a collection of additional data questions for a service.

    This model defines a set of configurable questions that can be asked
    when creating or updating requests, along with metadata about
    required variables and platform integration.
    """

    required_variables: list[str] | None = Field(
        default=None,
        alias="requiredVariables",
        description="List of variable names that must be provided to use this additional data set.",
    )
    configurable_questions: list[ConfigurableQuestion] | None = Field(
        default=None,
        description="List of questions with their configuration.",
    )
    id: str | None = Field(
        default=None,
        description="Unique identifier for the additional data set.",
    )
    name: str | None = Field(
        default=None,
        description="Name of the additional data set.",
    )
    description: str | None = Field(
        default=None,
        description="Description of what this additional data set is used for.",
    )


class PossibleAnswer(ImmutableBaseModel):
    """
    Represents a possible answer option for a singleValueList-type or multiValueList-type question.

    When a question has predefined answers, each option is represented by this model.
    Selecting an answer may trigger additional questions based on the conditional logic.
    """

    value: str | None = Field(
        default=None,
        description="The value of the answer option.",
    )
    next_question_list: AdditionalData | None = Field(
        default=None,
        description="Additional questions if this answer is selected.",
    )


class AdditionalDataAnswer(ImmutableBaseModel):
    """
    Represents an answer provided to an additional data question.

    This model contains the user's response to a configurable question,
    including the question details and the value provided.
    """

    type: str | None = Field(
        default=None,
        description=(
            "The type of answer value (label, number, boolean, color, datetime, "
            "position, singleValueList, multiValueList, url, signature, image, "
            "imageGallery, audioClip or videoClip)."
        ),
    )
    value: Any | None = Field(
        default=None,
        description="The answer value, which can be of various types depending on the question type.",
    )
    question: Question | None = Field(
        default=None,
        description="The question that this answer corresponds to.",
    )


class AdditionalDataValue(ImmutableBaseModel, ABC):
    """
    Base model for additional data values when creating or updating requests.

    This abstract model provides the foundation for different types of additional
    data values that can be submitted with requests.
    """

    question_id: str = Field(
        validation_alias=AliasChoices("question_id", "question"),
        serialization_alias="question",
        description="Unique identifier of the question this value answers.",
    )


class AdditionalDataSingleValue(AdditionalDataValue):
    """
    Represents a single-value answer to an additional data question.

    This model is used when submitting answers that accept a single text value.
    """

    value: str = Field(
        description="The single text value answering the question.",
    )


class AdditionalDataMultivalue(AdditionalDataValue):
    """
    Represents a multi-value answer to an additional data question.

    This model is used when submitting answers that accept multiple values.
    """

    value: Sequence[str] = Field(
        description="List of selected values answering the question.",
    )


class AdditionalDataDatetime(AdditionalDataValue):
    """
    Represents a datetime answer to an additional data question.

    This model is used when submitting date or datetime values as answers,
    automatically serialized to ISO format with timezone.
    """

    value: DatetimeField = Field(
        description="The datetime value answering the question, serialized in ISO format with timezone.",
    )


class AdditionalDataLocation(AdditionalDataValue):
    """
    Represents a geographic location answer to an additional data question.

    This model is used when submitting location coordinates as answers.
    The coordinates are stored separately but serialized as a nested object
    in the value field.
    """

    lat: float = Field(
        exclude=True,
        description="Latitude coordinate.",
    )
    lng: float = Field(
        exclude=True,
        description="Longitude coordinate.",
    )
    srs: str | None = Field(
        default="3857",
        exclude=True,
        description="Spatial Reference System identifier, default is '3857'.",
    )

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        data = super().model_dump(*args, **kwargs)
        data["value"] = {
            "lat": self.lat,
            "lng": self.lng,
            "srs": self.srs,
        }
        return data


class AdditionalDataAudioClip(AdditionalDataValue):
    """
    Represents an audio clip answer to an additional data question.

    This model is used when submitting audio file references as answers.
    """

    value: str = Field(
        description="The audio clip URL to be submitted as the answer.",
    )

    @field_serializer("value")
    def s(self, value: str) -> dict[str, dict[str, str]]:
        return {"audio_clip": {"es": value}}


class AdditionalDataVideoClip(AdditionalDataValue):
    """
    Represents a video clip answer to an additional data question.

    This model is used when submitting video file references as answers.
    """

    value: str = Field(
        description="The video clip URL to be submitted as the answer.",
    )

    @field_serializer("value")
    def s(self, value: str) -> dict[str, dict[str, str]]:
        return {"video_clip": {"es": value}}


class LocationAdditionalData(ImmutableBaseModel):
    """
    Represents location-specific additional data and questions.

    This model contains additional data questions that are specific to a particular
    location, including the formatted address and geographic coordinates.
    """

    formatted_address: str | None = Field(
        default=None,
        description="The formatted address string of the location.",
    )
    data: list[AdditionalDataAnswer] | None = Field(
        default=None,
        description="List of additional data answers associated with this location.",
    )
    location: Location | None = Field(
        default=None,
        description="The geographic coordinates of the location.",
    )


class LocationAdditionalDataList(RootModel[list[LocationAdditionalData]]):
    """
    A collection of LocationAdditionalData objects.

    This model represents a list of location-specific additional data returned
    when querying location-based information for a jurisdiction element.
    """

    pass
