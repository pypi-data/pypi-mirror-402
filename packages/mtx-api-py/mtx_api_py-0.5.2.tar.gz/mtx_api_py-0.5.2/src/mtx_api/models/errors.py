# Modelos y excepciones de error extraídos de models.py
import json

from pydantic import AliasChoices, Field, ValidationError

from mtx_api.models.base import ImmutableBaseModel


class ApiErrorReason(ImmutableBaseModel):
    """
    Represents detailed information about an error from the platform.

    This model captures the complete error context including HTTP status code,
    platform-specific error code, and a human-readable description. It is used
    to provide structured error information when operations fail.
    """

    status_code: int = Field(
        description="The HTTP status code of the error response (e.g., 400, 404, 500).",
    )
    code: int | None = Field(
        default=None,
        validation_alias=AliasChoices("error_code", "code"),
        description="Platform-specific error code for programmatic error handling.",
    )
    description: str | None = Field(
        default=None,
        validation_alias=AliasChoices("error_msg", "description", "message"),
        description="Human-readable description of the error explaining what went wrong.",
    )


class ApiError(Exception):
    def __init__(self, body: str, status_code: int):
        super().__init__()
        self.reason = self.parse_reason(body, status_code)

    @staticmethod
    def parse_reason(body: str, status_code: int) -> ApiErrorReason | None:
        if body:
            try:
                obj = json.loads(body)
                if isinstance(obj, list):
                    obj = obj[0] if obj else {}
                if obj is None or not isinstance(obj, dict):
                    obj = {}
                if "status_code" not in obj:
                    obj["status_code"] = status_code
                reason = ApiErrorReason.model_validate(obj)
            except (ValidationError, ValueError):
                reason = ApiErrorReason(description=str(body), status_code=status_code)
        else:
            reason = ApiErrorReason(status_code=status_code)
        return reason

    @property
    def code(self) -> int | None:
        return self.reason.code if self.reason else None

    @property
    def description(self) -> str | None:
        return self.reason.description if self.reason else None

    @property
    def status_code(self) -> int | None:
        return self.reason.status_code if self.reason else None

    def __str__(self) -> str:
        parts = []
        if self.status_code:
            parts.append(str(self.status_code))
        if self.code:
            parts.append(str(self.code))
        if self.description:
            parts.append(self.description)
        return " ".join(parts)


class ApiDecodingError(Exception):
    pass


class InvalidEmailError(ValueError):
    pass


class MissingBaseUrlError(ValueError):
    pass


class MissingClientIdError(ValueError):
    pass


class MissingJwtSecretError(ValueError):
    pass


class MissingJurisdictionCodesError(ValueError):
    pass


class MissingServiceIdError(ValueError):
    pass


class MissingRequestIdError(ValueError):
    pass


class MissingJurisdictionElementIdError(ValueError):
    pass


class MissingArgumentError(ValueError):
    def __init__(self, arg: str):
        super().__init__(arg)
