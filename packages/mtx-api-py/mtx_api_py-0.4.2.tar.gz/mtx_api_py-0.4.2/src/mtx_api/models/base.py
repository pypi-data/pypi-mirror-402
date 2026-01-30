from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, PlainSerializer


class ImmutableBaseModel(BaseModel):
    model_config = {
        "frozen": True,
    }


class EmptyResponse(ImmutableBaseModel):
    pass


class TextResponse(ImmutableBaseModel):
    text: str


DatetimeField = Annotated[
    datetime,
    PlainSerializer(
        lambda v: v.astimezone(UTC).isoformat() if v else None,
    ),
]
