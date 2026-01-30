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

## Available functions

All available functions accept their parameters as keyword arguments.
You can omit arguments that are not needed and accept None.

### client.base:

```
status(
  access_token: str | None
) -> bool
```
```
openapi() -> str
```

### client.auth:

```
login_anonymous(
  device_id: str
) -> Authentication
```
```
login_jwt(
  email: str,
  first_name: str | None,
  last_name: str | None,
  register: bool | None,
  legal_terms_accepted: bool | None
) -> Authentication
```
```
login_refresh(
  refresh_token: str
) -> Authentication
```
```
register(
  username: str,
  password: str,
  first_name: str,
  last_name: str,
  legal_terms_accepted: bool,
  jurisdiction_code: str | None
) -> Authentication
```
```
login(
  username: str,
  password: str
) -> Authentication
```

### client.user:

```
profile(
  access_token: str | None
) -> Profile
```
```
update_profile(
  access_token: str | None,
  email: str | None,
  username: str | None,
  first_name: str | None,
  last_name: str | None,
  twitter_nickname: str | None,
  phone: str | None,
  gender: str | None,
  birthday: str | None
) -> Profile
```

```
accept_terms(
  access_token: str
) -> bool
```
```
legal_terms() -> LegalTerms
```

### client.services:

```
list(
  access_token: str | None,
  jurisdiction_codes: list[str],
  lat: float | None,
  lng: float | None,
  typology_ids: list[str] | None
) -> ServiceList
```
```
detail(
  access_token: str | None,
  service_id: str,
  jurisdiction_code: str
) -> Service
```

### client.typologies:

```
list(
  access_token: str | None,
  jurisdiction_codes: list[str],
  jurisdiction_element_id: str | None,
  typology_ids: list[str] | None,
  lat: float | None,
  lng: float | None,
  page: int | None,
  limit: int | None
) -> TypologyList
```
### client.jurisdictions:
```
list(
  access_token: str | None,
  lat: float | None,
  lng: float | None
) -> JurisdictionList
```
```
detail(
  access_token: str | None,
  jurisdiction_code: str
) -> Jurisdiction
```
### client.jurisdiction_elements:
```
list(
  access_token: str | None,
  jurisdiction_code: str
) -> JurisdictionElementList
```

### client.location:
```
resolve(
  jurisdiction_element_id: str,
  formatted_address: str | None,
  lat: float | None,
  lng: float | None
) -> LocationAdditionalDataList
```

### client.requests:

```
list(
  access_token: str | None,
  jurisdiction_codes: list[str] | None,
  service_request_ids: list[str] | None,
  service_ids: list[str] | None,
  start_date: str | None,
  end_date: str | None,
  own: bool | None,
  lat: float | None,
  lng: float | None,
  page: int | None,
  limit: int | None,
  address_and_service_request_id: str | None,
  status: list[str] | None,
  typology_ids: list[str] | None,
  distance: int | None,
  following: bool | None,
  order: str | None,
  complaints: bool | None,
  reiterations: bool | None,
  user_reiterated: bool | None,
  user_complaint: bool | None,
  jurisdiction_element_ids: list[str] | None,
  level: int | None,
  polygon: list[float] | None,
  final_ok: bool | None,
  final_not_ok: bool | None,
  final_status: bool | None,
  interested: bool | None,
  timezone: str | None
) -> RequestList
```
```
detail(
  access_token: str | None,
  request_id: str
) -> Request
```
```
create(
  access_token: str | None,
  service_id: str,
  jurisdiction_code: str,
  jurisdiction_element_id: str | None,
  origin_device_id: str | None,
  description: str | None,
  public: bool | None,
  lat: float | None,
  lng: float | None,
  address_string: str | None,
  email: str | None,
  first_name: str | None,
  last_name: str | None,
  phone: str | None,
  twitter_nickname: str | None,
  additional_data: Sequence[AdditionalDataValue] | None
) -> CreatedRequest
```
```
attach_media(
  access_token: str | None,
  request_id: str,
  jurisdiction_code: str,
  file: tuple[str, bytes]
) -> RequestMedia
```
```
attach_comment(
  access_token: str | None,
  request_id: str,
  comment: str | None,
  files: Sequence[tuple[str, bytes]]
) -> RequestComment
```

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
