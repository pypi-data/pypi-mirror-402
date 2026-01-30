# MTX API PY

Python SDK (wrapper) to consume the MTX API.

## Installation

```bash
pip install mtx-api-py
```

## Quick start

```python
import asyncio
from mtx_api import MTXClient


async def main():
    async with MTXClient(
            base_url="https://api.mtx.example.com",
            client_id="YOUR_CLIENT_ID",
            jwt_secret="BASE64_SECRET",  # optional; only if you will use auth.login_jwt
    ) as client:
        ok = await client.base.status(access_token="<ACCESS_TOKEN>")
        print(ok)


asyncio.run(main())
```

## Configure via environment variables (.env)

You can configure the client using environment variables or a `.env` file at the project root:

```bash
# .env
MTX_BASE_URL=https://api.mtx.example.com
MTX_CLIENT_ID=YOUR_CLIENT_ID
MTX_JWT_SECRET=BASE64_SECRET # Optional: only needed if you will use login_jwt
```

```python
import asyncio
from mtx_api import MTXClient
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


async def main():
    async with MTXClient() as client:
        ok = await client.base.status(access_token="<ACCESS_TOKEN>")
        print(ok)


asyncio.run(main())
```

# MTX Client Reference

All available functions accept their parameters as keyword arguments.
You can omit arguments that are not needed and accept None.

## auth

### login

#### Signature
```python
auth.login(*, username: str, password: str) -> mtx_api.models.auth.Authentication
```

#### Docstring
Authenticates a user using their username (email) and password.

Use this tool for standard user login to obtain access credentials.

**Args:**
- **username (str)**: The user's email address.
- **password (str)**: The user's password.

**Returns:**
- **Authentication**: A model containing access and refresh tokens.

**Raises:**
- **MissingArgumentError**: If `username` or `password` is missing.

### login_anonymous

#### Signature
```python
auth.login_anonymous(*, device_id: str) -> mtx_api.models.auth.Authentication
```

#### Docstring
Authenticates a user anonymously using a unique device identifier.

Use this tool to log in a user who does not have a registered account,
identifying them solely by their device ID. This enables access to
features that require authentication without user registration.

**Args:**
- **device_id (str)**: A stable and unique identifier for the device.

**Returns:**
- **Authentication**: A model containing access and refresh tokens.

**Raises:**
- **MissingArgumentError**: If `device_id` is empty or None.

### login_jwt

#### Signature
```python
auth.login_jwt(*, email: str, first_name: str | None = None, last_name: str | None = None, register: bool | None = None, legal_terms_accepted: bool | None = None) -> mtx_api.models.auth.Authentication
```

#### Docstring
Authenticates a user using a signed JSON Web Token (JWT).

Use this tool for trusted server-side authentication or Single Sign-On (SSO)
integration. It facilitates logging in or registering a user based on their
email address.

**Args:**
- **email (str)**: The user's email address.
- **first_name (str, opcional)**: Optional user's first name. Defaults to None.
- **last_name (str, opcional)**: Optional user's last name. Defaults to None.
- **register (bool, opcional)**: Optional. If True, registers the user if they do not exist.
  Defaults to None.
- **legal_terms_accepted (bool, opcional)**: Optional. Whether the user has accepted the
  legal terms. Defaults to None.

**Returns:**
- **Authentication**: A model containing access and refresh tokens.

**Raises:**
- **InvalidEmailError**: If the provided email format is invalid.
- **MissingJwtSecretError**: If the JWT secret is not configured in the client.

### login_refresh

#### Signature
```python
auth.login_refresh(*, refresh_token: str) -> mtx_api.models.auth.Authentication
```

#### Docstring
Refreshes an existing authentication session using a valid refresh token.

Use this tool to obtain a new access token when the current one has expired,
allowing the user's session to continue without requiring re-authentication.

**Args:**
- **refresh_token (str)**: The token issued during a previous authentication, used
  to refresh the session.

**Returns:**
- **Authentication**: A model containing access and refresh tokens.

**Raises:**
- **MissingArgumentError**: If `refresh_token` is empty or None.

### register

#### Signature
```python
auth.register(*, username: str, password: str, first_name: str, last_name: str, legal_terms_accepted: bool, jurisdiction_code: str | None = None) -> mtx_api.models.auth.Authentication
```

#### Docstring
Registers a new user account and immediately authenticates the user.

Use this tool to create a new user profile with the provided credentials
and personal information. This action also logs the user in.

**Args:**
- **username (str)**: The email address to use as the username.
- **password (str)**: The password for the new account.
- **first_name (str)**: The user's first name.
- **last_name (str)**: The user's last name.
- **legal_terms_accepted (bool)**: Must be True to indicate acceptance of legal terms.
- **jurisdiction_code (str, opcional)**: Optional jurisdiction code for the user.
  Defaults to None.

**Returns:**
- **Authentication**: A model containing access and refresh tokens.

**Raises:**
- **MissingArgumentError**: If any required argument (username, password,
  first_name, last_name) is missing.

## base

### openapi

#### Signature
```python
base.openapi() -> 'str'
```

#### Docstring
Retrieves the OpenAPI specification of the platform.

Fetches the complete OpenAPI documentation in plain text. This provides details on available
tools, operation structures, and expected responses.

**Returns:**
- **str**: The OpenAPI document content as a string.

### status

#### Signature
```python
base.status(*, access_token: 'str | None' = None) -> 'bool'
```

#### Docstring
Checks the operational status of the platform.

Verifies if the platform is running and reachable. Use this tool
to confirm platform availability before performing other operations.

**Args:**
- **access_token**: Optional token used for authentication. If not provided, the operation
  will be made without authentication.

**Returns:**
- **bool**: True if the platform is available and the operation succeeds.

## jurisdiction_elements

### list

#### Signature
```python
jurisdiction_elements.list(*, access_token: str | None = None, jurisdiction_code: str) -> mtx_api.models.jurisdiction.JurisdictionElementList
```

#### Docstring
Retrieves jurisdiction elements associated with a specific jurisdiction code.

Use this tool to find all jurisdiction elements linked to a given jurisdiction code
from the platform.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided,
  the operation will be made without authentication. Defaults to None.
- **jurisdiction_code (str)**: The unique string code of the jurisdiction to query.

**Returns:**
- **JurisdictionElementList**: An object containing the list of retrieved
  jurisdiction elements.

**Raises:**
- **MissingJurisdictionCodesError**: If the `jurisdiction_code` argument is missing or empty.

## jurisdictions

### detail

#### Signature
```python
jurisdictions.detail(*, access_token: 'str | None' = None, jurisdiction_code: 'str') -> 'Jurisdiction'
```

#### Docstring
Retrieves detailed information for a specific jurisdiction.

This tool fetches the complete details of a jurisdiction using its unique code.
Use this tool when you need more information about a specific jurisdiction than what is
provided in the list.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided,
  the operation will be made without authentication. Defaults to None.
- **jurisdiction_code (str)**: The unique string code of the jurisdiction to query.

**Returns:**
- **Jurisdiction**: An object containing comprehensive information about the jurisdiction.

**Raises:**
- **MissingJurisdictionCodesError**: If the provided jurisdiction_code is empty.

### list

#### Signature
```python
jurisdictions.list(*, access_token: 'str | None' = None, lat: 'float | None' = None, lng: 'float | None' = None) -> 'JurisdictionList'
```

#### Docstring
Retrieves a list of jurisdictions from the platform.

This tool allows you to list all available jurisdictions or find those closest to a
specific location if coordinates are provided.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided,
  the operation will be made without authentication. Defaults to None.
- **lat (float, opcional)**: Optional latitude coordinate to filter jurisdictions by
  proximity. Defaults to None.
- **lng (float, opcional)**: Optional longitude coordinate to filter jurisdictions by
  proximity. Defaults to None.

**Returns:**
- **JurisdictionList**: A collection of Jurisdiction objects with basic details.

## location

### resolve

#### Signature
```python
location.resolve(*, jurisdiction_element_id: str, formatted_address: str | None = None, lat: float | None = None, lng: float | None = None) -> mtx_api.models.additional_data.LocationAdditionalDataList
```

#### Docstring
Retrieves latitude and longitude information from an address, or vice versa.

This tool fetches location-specific questions configured for a
jurisdiction element. You can identify the location by providing either a formatted
address, geographic coordinates (lat, lng), or both. Regardless of which parameters
you provide, the tool always returns the complete location information including
formatted address, geographic coordinates, and the list of additional data questions.

Use this tool when you need to know what additional information should be collected
for a specific location.

**Args:**
- **jurisdiction_element_id (str)**: The unique identifier string of the jurisdiction element
  where the location is being queried.
- **formatted_address (str, opcional)**: Optional complete address string in human-readable
  format to identify the location. Defaults to None.
- **lat (float, opcional)**: Optional latitude coordinate as a decimal number to identify
  the location. Must be provided together with lng. Defaults to None.
- **lng (float, opcional)**: Optional longitude coordinate as a decimal number to identify
  the location. Must be provided together with lat. Defaults to None.

**Returns:**
- **LocationAdditionalDataList**: A collection of location entries. Each entry always
  contains the formatted address, geographic coordinates (latitude and longitude),
  and a list of additional data questions configured for that location, regardless
  of which input parameters were used to identify the location.

**Raises:**
- **MissingJurisdictionElementIdError**: If jurisdiction_element_id is empty or not provided.

## requests

### attach_comment

#### Signature
```python
requests.attach_comment(*, access_token: 'str | None' = None, request_id: 'str', comment: 'str | None' = None, files: 'Sequence[tuple[str, bytes]]' = ()) -> 'RequestComment'
```

#### Docstring
Attach a comment to an existing request.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided, the operation
  will be made without authentication. Defaults to None.
- **request_id (str)**: The identifier of the request to which the comment will be added.
- **Note**: this is the internal request `id`, not the `service_request_id`.
- **comment (str, opcional)**: Optional text of the comment. Can be empty. Defaults to None.
- **files (Sequence[tuple[str, bytes]], opcional)**: Optional sequence of files to attach with the comment.
  Each file is a tuple containing the file name (str) and the file content (bytes). Defaults to ().

**Returns:**
- **RequestComment**: The created comment object.

**Raises:**
- **MissingRequestIdError**: If request_id is missing.

### attach_media

#### Signature
```python
requests.attach_media(*, access_token: 'str | None' = None, request_id: 'str', jurisdiction_code: 'str', file: 'tuple[str, bytes]') -> 'RequestMedia'
```

#### Docstring
Attach a media file to an existing request.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided, the operation
  will be made without authentication. Defaults to None.
- **request_id (str)**: The identifier of the request to which the media will be attached.
- **Note**: this is the internal request `id`, not the `service_request_id`.
- **jurisdiction_code (str)**: The code of the jurisdiction associated with the request.
- **file (tuple[str, bytes])**: A tuple containing the file name (str) and the file content (bytes).

**Returns:**
- **RequestMedia**: The object representing the attached media.

**Raises:**
- **MissingRequestIdError**: If request_id is missing.
- **MissingJurisdictionCodesError**: If jurisdiction_code is missing.
- **MissingArgumentError**: If file content or file name is empty, or if extension is missing.

### create

#### Signature
```python
requests.create(*, access_token: 'str | None' = None, service_id: 'str', jurisdiction_code: 'str', jurisdiction_element_id: 'str | None' = None, origin_device_id: 'str | None' = None, description: 'str | None' = None, public: 'bool | None' = None, lat: 'float | None' = None, lng: 'float | None' = None, address_string: 'str | None' = None, email: 'str | None' = None, first_name: 'str | None' = None, last_name: 'str | None' = None, phone: 'str | None' = None, twitter_nickname: 'str | None' = None, additional_data: 'Sequence[AdditionalDataValue] | None' = None) -> 'CreatedRequest'
```

#### Docstring
Create a new request in the platform.

This function allows creating a new request (issue report) within a specific jurisdiction.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided,
  the operation will be made without authentication. Defaults to None.
- **service_id (str)**: Identifier of the service to request.
- **jurisdiction_code (str)**: Code of the jurisdiction where the request is made.
- **jurisdiction_element_id (str, opcional)**: Optional ID of a specific element within the
  jurisdiction. Defaults to None.
- **origin_device_id (str, opcional)**: Optional ID of the device making the request.
  Can be found on Jurisdiction detail. Defaults to None.
- **description (str, opcional)**: Optional textual description of the request.
  Defaults to None.
- **public (bool, opcional)**: Optional boolean. If True, the request is public; if False,
  it is private. Defaults to None.
- **lat (float, opcional)**: Optional latitude coordinate of the request location.
  Defaults to None.
- **lng (float, opcional)**: Optional longitude coordinate of the request location.
  Defaults to None.
- **address_string (str, opcional)**: Optional physical address associated with the request.
  Defaults to None.
- **email (str, opcional)**: Optional email address of the person making the request.
  Defaults to None.
- **first_name (str, opcional)**: Optional first name of the person making the request.
  Defaults to None.
- **last_name (str, opcional)**: Optional last name of the person making the request.
  Defaults to None.
- **phone (str, opcional)**: Optional phone number of the person making the request.
  Defaults to None.
- **twitter_nickname (str, opcional)**: Optional Twitter handle of the person making the
  request. Defaults to None.
- **additional_data (Sequence[AdditionalDataValue], opcional)**: Optional sequence of additional
  data values required by the service. Defaults to None.

**Returns:**
- **CreatedRequest**: The created request instance with its details.

**Raises:**
- **MissingJurisdictionCodesError**: If jurisdiction_code is missing.
- **MissingServiceIdError**: If service_id is missing.

### detail

#### Signature
```python
requests.detail(*, access_token: 'str | None' = None, request_id: 'str') -> 'Request'
```

#### Docstring
Retrieve detailed information about a specific request.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided, the operation
  will be made without authentication. Defaults to None.
- **request_id (str)**: The unique identifier of the request to fetch.
- **Note**: this is the internal request `id`, not the `service_request_id`.

**Returns:**
- **Request**: The detailed Request object containing all information.

**Raises:**
- **MissingRequestIdError**: If request_id is missing.

### list

#### Signature
```python
requests.list(*, access_token: 'str | None' = None, jurisdiction_codes: 'list[str] | None' = None, service_request_ids: 'list[str] | None' = None, service_ids: 'list[str] | None' = None, start_date: 'str | None' = None, end_date: 'str | None' = None, own: 'bool | None' = None, lat: 'float | None' = None, lng: 'float | None' = None, page: 'int | None' = None, limit: 'int | None' = None, address_and_service_request_id: 'str | None' = None, status: 'list[str] | None' = None, typology_ids: 'list[str] | None' = None, distance: 'int | None' = None, following: 'bool | None' = None, order: 'str | None' = None, complaints: 'bool | None' = None, reiterations: 'bool | None' = None, user_reiterated: 'bool | None' = None, user_complaint: 'bool | None' = None, jurisdiction_element_ids: 'list[str] | None' = None, level: 'int | None' = None, polygon: 'list[float] | None' = None, final_ok: 'bool | None' = None, final_not_ok: 'bool | None' = None, final_status: 'bool | None' = None, interested: 'bool | None' = None, timezone: 'str | None' = None) -> 'RequestList'
```

#### Docstring
List and filter requests from the platform.

This function retrieves a list of requests based on multiple filtering criteria.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided,
  the operation will be made without authentication. Defaults to None.
- **jurisdiction_codes (list[str], opcional)**: Optional list of jurisdiction codes to filter by.
  Defaults to None.
- **service_request_ids (list[str], opcional)**: Optional list of specific request IDs to retrieve.
  Defaults to None.
- **service_ids (list[str], opcional)**: Optional list of service IDs to filter by. Defaults to None.
- **start_date (str, opcional)**: Optional ISO date-time string (inclusive) to filter requests created
  after this date. Defaults to None.
- **end_date (str, opcional)**: Optional ISO date-time string (inclusive) to filter requests created
  before this date. Defaults to None.
- **own (bool, opcional)**: Optional boolean. If True, returns only requests created by the
  authenticated user. Defaults to None.
- **lat (float, opcional)**: Optional latitude to be used for distance filtering or ordering by
  proximity. Defaults to None.
- **lng (float, opcional)**: Optional longitude to be used for distance filtering or ordering by
  proximity. Defaults to None.
- **page (int, opcional)**: Optional page number for pagination. Defaults to None.
- **limit (int, opcional)**: Optional number of items per page. Defaults to None.
- **address_and_service_request_id (str, opcional)**: Optional free text search for address or
  service request ID. Defaults to None.
- **status (list[str], opcional)**: Optional list of status codes to filter by. Defaults to None.
- **typology_ids (list[str], opcional)**: Optional list of typology IDs to filter by. Defaults to None.
- **distance (int, opcional)**: Optional radius in meters to filter requests around the provided
  lat/lng. Defaults to None.
- **following (bool, opcional)**: Optional boolean. If True, returns only requests followed by the
  authenticated user. Defaults to None.
- **order (str, opcional)**: Optional ordering strategy (e.g., "newest_date_desc"). Defaults to None.
- **complaints (bool, opcional)**: Optional boolean. If True, filters only complaints.
  Defaults to None.
- **reiterations (bool, opcional)**: Optional boolean. If True, filters only reiterations.
  Defaults to None.
- **user_reiterated (bool, opcional)**: Optional boolean. If True, filters requests reiterated by
  the authenticated user. Defaults to None.
- **user_complaint (bool, opcional)**: Optional boolean. If True, filters complaints made by the
  authenticated user. Defaults to None.
- **jurisdiction_element_ids (list[str], opcional)**: Optional list of jurisdiction element IDs to
  filter by. Defaults to None.
- **level (int, opcional)**: Optional floor level to filter by. Defaults to None.
- **polygon (list[float], opcional)**: Optional list of float coordinates describing a polygon area
  to filter requests within. Defaults to None.
- **final_ok (bool, opcional)**: Optional boolean. If True, filters requests with a final
  status of OK. Defaults to None.
- **final_not_ok (bool, opcional)**: Optional boolean. If True, filters requests with a final
  status of NOT OK. Defaults to None.
- **final_status (bool, opcional)**: Optional boolean. If True, filters requests with any
  final status. Defaults to None.
- **interested (bool, opcional)**: Optional boolean. If True, filters requests where the user has
  expressed interest. Defaults to None.
- **timezone (str, opcional)**: Optional IANA timezone string used by the backend for date filtering.
  Defaults to None.

**Returns:**
- **RequestList**: A list of Request items matching the criteria.

## services

### detail

#### Signature
```python
services.detail(*, access_token: str | None = None, service_id: str, jurisdiction_code: str) -> mtx_api.models.service.Service
```

#### Docstring
Retrieves the detailed information of a specific service.

This function fetches the full details of a service identified by its ID
within a specific jurisdiction. Details include additional_data and other
relevant information.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided, the operation
  will be made without authentication. Defaults to None.
- **service_id (str)**: The identifier of the service to fetch details for.
- **jurisdiction_code (str)**: The jurisdiction code where the service is located.

**Returns:**
- **Service**: The detailed information of the requested service.

**Raises:**
- **MissingJurisdictionCodesError**: If the jurisdiction code is not provided.
- **MissingServiceIdError**: If the service ID is not provided.

## typologies

## user

### accept_terms

#### Signature
```python
user.accept_terms(*, access_token: str) -> bool
```

#### Docstring
Accepts the legal terms and conditions for the currently authenticated user.

Use this tool to register the acceptance of legal terms for a previously
registered user. Accepting these terms allows the user to use the platform.
If not accepted, the user will not be allowed to use the platform.

Should be used if a 451 error is received.

**Args:**
- **access_token (str)**: Optional token used for authentication. If not provided,
  the operation will be made without authentication.

**Returns:**
- **bool**: True if the terms were successfully accepted.

### legal_terms

#### Signature
```python
user.legal_terms() -> mtx_api.models.common.LegalTerms
```

#### Docstring
Retrieves the current legal terms and conditions content.

Use this function to fetch the complete legal terms and conditions content
that users must accept to use the platform. The returned content may include
plain text, formatted text, or links to external legal documents. This is
typically given to users during registration or when terms have been
updated and require re-acceptance.

**Returns:**
- **LegalTerms**: A model containing the legal terms content, which may include
  privacy policy, terms of use, and cookies policy. Each field can
  contain text or links to legal documents.

### profile

#### Signature
```python
user.profile(*, access_token: str | None = None) -> mtx_api.models.auth.Profile
```

#### Docstring
Retrieves the profile information of the currently authenticated user.

Use this tool to fetch details about the current user, including personal
information and account settings.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided,
  the operation will be made without authentication. Defaults to None.

**Returns:**
- **Profile**: A model containing the user's profile details.

### update_profile

#### Signature
```python
user.update_profile(*, access_token: str | None = None, email: str | None = None, username: str | None = None, first_name: str | None = None, last_name: str | None = None, twitter_nickname: str | None = None, phone: str | None = None, gender: Gender | None = None, birthday: str | None = None) -> mtx_api.models.auth.Profile
```

#### Docstring
Updates the profile information of the currently authenticated user.

Use this tool to modify the personal details and account information of
the user. Only the fields provided will be updated; fields set to None
will remain unchanged.

**Args:**
- **access_token (str, opcional)**: Optional token used for authentication. If not provided,
  the operation will be made without authentication. Defaults to None.
- **email (str, opcional)**: Optional new email address for the user. Defaults to None.
- **username (str, opcional)**: Optional new username for the user, typically their email
  address. Defaults to None.
- **first_name (str, opcional)**: Optional new first name or given name for the user.
  Defaults to None.
- **last_name (str, opcional)**: Optional new last name or family name for the user.
  Defaults to None.
- **twitter_nickname (str, opcional)**: Optional new shown name or twitter_nickname visible to
  others. Defaults to None.
- **phone (str, opcional)**: Optional new primary phone number for contact purposes.
  Defaults to None.
- **gender (Gender, opcional)**: Optional new gender identification for the user.
  Defaults to None.
- **birthday (str, opcional)**: Optional new date of birth in format YYYY-MM-DD.
  Defaults to None.

**Returns:**
- **Profile**: A model containing the updated user's profile details.



## Errors

- HTTP errors raise `ApiError` with fields `status_code`, `code`, and `description`.
- Response model decoding/validation errors raise `ApiDecodingError`.
- SDK parameter validation errors raise specific exceptions (all extend `ValueError`):
  - `MissingBaseUrlError`: missing `base_url` configuration (via `MTX_BASE_URL` or `base_url` parameter).
  - `MissingClientIdError`: missing `client_id` configuration (via `MTX_CLIENT_ID` or `client_id` parameter).
  - `MissingJwtSecretError`: missing JWT secret configuration (via `MTX_JWT_SECRET` or `jwt_secret` parameter) when using `auth.login_jwt`.
  - `MissingJurisdictionCodesError`: missing `jurisdiction_codes`/`jurisdiction_code` in calls that require it.
  - `MissingServiceIdError`: missing `service_id` in calls that require it.
  - `MissingRequestIdError`: missing `request_id` in calls that require it.
  - `MissingArgumentError`: a required argument is missing.
  - `InvalidEmailError`: the email is not valid.
