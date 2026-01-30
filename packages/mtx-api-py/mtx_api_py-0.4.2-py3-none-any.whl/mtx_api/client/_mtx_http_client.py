from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from enum import Enum
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from mtx_api.models.base import EmptyResponse, TextResponse
from mtx_api.models.errors import (
    ApiDecodingError,
    ApiError,
    MissingBaseUrlError,
    MissingClientIdError,
)
from mtx_api.settings import MTXSettings

M = TypeVar("M", bound=BaseModel)


class Method(Enum):
    PUT = "PUT"
    GET = "GET"
    POST = "POST"


class MtxHttpClient:
    def __init__(
        self,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        base_url: str | None = None,
        client_id: str | None = None,
        jwt_secret: str | None = None,
    ) -> None:
        settings = MTXSettings()

        base_url_value = base_url or settings.base_url
        if not base_url_value:
            raise MissingBaseUrlError()
        self._base_url: str = base_url_value.rstrip("/")

        client_id_value = client_id or settings.client_id
        if not client_id_value:
            raise MissingClientIdError()
        self._client_id: str = client_id_value

        self._jwt_secret: str | None = jwt_secret or settings.jwt_secret

        logging.getLogger("httpx").setLevel(logging.WARNING)
        self.logger = logging.getLogger("mtx_logs")

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            transport=transport,
            follow_redirects=True,
        )

    async def __aenter__(self) -> MtxHttpClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None,
    ) -> None:
        await self._client.aclose()

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def jwt_secret(self) -> str | None:
        return self._jwt_secret

    async def http_request(
        self,
        *,
        method: Method,
        path: str,
        model: type[M],
        access_token: str | None = None,
        headers: Mapping[str, str] | None = None,
        body: Mapping[str, object] | None = None,
        query_params: Mapping[str, object] | None = None,
        files: Mapping[str, tuple[str, bytes]] | None = None,
    ) -> M:
        if not path.startswith("/"):
            path = f"/{path}"
        try:
            auth_header = {"Authorization": f"Bearer {access_token}"} if access_token else {}
            headers = {
                **auth_header,
                **(headers or {}),
                "X-CLIENT-ID": self._client_id,
            }

            is_multipart = files is not None

            if not is_multipart:
                headers["Content-type"] = "application/json"

            def normalize(value: object) -> str | None:
                if value is None:
                    return None
                if isinstance(value, bool):
                    return "true" if value else "false"
                if isinstance(value, list):
                    return ",".join(map(str, value)) if value else None
                return str(value)

            params = {k: normalize(v) for k, v in query_params.items()} if query_params else None

            body = {k: v for k, v in body.items() if v is not None} if body else None

            req = self._client.build_request(
                method=method.value,
                url=path,
                headers=headers,
                json=body if body and not is_multipart else None,
                data=body if body and is_multipart else None,
                params={k: v for k, v in params.items() if v is not None} if params else None,
                files=files,
            )

            if is_multipart:
                req.extensions["mtx_file_names"] = files
                req.extensions["mtx_form_fields"] = body

            self.log_as_curl(req)
            resp = await self._client.send(req)
            resp.raise_for_status()
            self.log_response(resp)
            try:
                if model is EmptyResponse:
                    return model()
                elif model is TextResponse:
                    return model(text=resp.text)
                else:
                    return model.model_validate_json(resp.text)
            except (ValidationError, ValueError) as de:
                raise ApiDecodingError(str(de))
        except httpx.HTTPStatusError as e:
            resp = e.response
            api_error = ApiError(body=resp.text, status_code=resp.status_code)
            self.log_error(api_error)
            raise api_error from e

    def log_as_curl(
        self,
        request: httpx.Request,
    ) -> None:
        header_parts = " ".join([f'-H "{k}: {v}"' for k, v in request.headers.items()])
        content_type = request.headers.get("content-type", "").lower()

        def replace_quotes(s: str) -> str:
            return s.replace("'", "'\"'\"'")

        data_part = ""
        if content_type.startswith("multipart/form-data"):
            extensions = request.extensions
            parts = []

            form_meta = extensions.get("mtx_form_fields") or {}
            parts.extend([f"{k}={v}" for k, v in form_meta.items()])

            files_meta = extensions.get("mtx_file_names") or {}
            parts.extend([f"{k}=@{v[0]}" for k, v in files_meta.items()])

            data_part = " ".join([f"-F '{replace_quotes(p)}'" for p in parts])
        elif request.content:
            data = request.content.decode()
            data_part = f" -d '{replace_quotes(data)}'"

        self.logger.info(f"HTTP {request.method} to {request.url.path}")
        self.logger.debug(f"curl -X {request.method} {str(request.url)} {header_parts} {data_part}")

    def log_response(self, resp: httpx.Response) -> None:
        try:
            json_obj = json.loads(resp.text)
            formatted_json = json.dumps(json_obj, indent=4)
            self.logger.debug(f"Response JSON: {resp.status_code} {formatted_json}")
        except json.JSONDecodeError:
            self.logger.debug(f"Response Text: {resp.status_code} {resp.text}")

    def log_error(self, e: ApiError) -> None:
        self.logger.error(f"{type(e).__name__}: {e}")


def array_query_param(key: str, value: Sequence[object] | None) -> dict[str, object]:
    return {} if value is None else {f"{key}[{i}]": v for i, v in enumerate(value)}
