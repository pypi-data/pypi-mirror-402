import re
from base64 import b64decode

import jwt

from mtx_api.client._mtx_http_client import Method, MtxHttpClient
from mtx_api.models.auth import Authentication
from mtx_api.models.errors import InvalidEmailError, MissingArgumentError, MissingJwtSecretError


class AuthClient:
    def __init__(self, client: MtxHttpClient):
        self._client: MtxHttpClient = client

    async def login_anonymous(
        self,
        *,
        device_id: str,
    ) -> Authentication:
        """
        Authenticates a user anonymously using a unique device identifier.

        Use this tool to log in a user who does not have a registered account,
        identifying them solely by their device ID. This enables access to
        features that require authentication without user registration.

        Args:
            device_id (str): A stable and unique identifier for the device.

        Returns:
            Authentication: A model containing access and refresh tokens.

        Raises:
            MissingArgumentError: If `device_id` is empty or None.
        """
        if not device_id:
            raise MissingArgumentError("device_id")

        return await self._client.http_request(
            method=Method.POST,
            path="login-anonymous",
            model=Authentication,
            body={
                "client_id": self._client.client_id,
                "device_id": device_id,
            },
        )

    async def login_refresh(
        self,
        *,
        refresh_token: str,
    ) -> Authentication:
        """
        Refreshes an existing authentication session using a valid refresh token.

        Use this tool to obtain a new access token when the current one has expired,
        allowing the user's session to continue without requiring re-authentication.

        Args:
            refresh_token (str): The token issued during a previous authentication, used
                to refresh the session.

        Returns:
            Authentication: A model containing access and refresh tokens.

        Raises:
            MissingArgumentError: If `refresh_token` is empty or None.
        """
        if not refresh_token:
            raise MissingArgumentError("refresh_token")
        return await self._client.http_request(
            method=Method.POST,
            path="oauth/v2/token",
            model=Authentication,
            body={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self._client.client_id,
            },
        )

    async def login_jwt(
        self,
        *,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        register: bool | None = None,
        legal_terms_accepted: bool | None = None,
    ) -> Authentication:
        """
        Authenticates a user using a signed JSON Web Token (JWT).

        Use this tool for trusted server-side authentication or Single Sign-On (SSO)
        integration. It facilitates logging in or registering a user based on their
        email address.

        Args:
            email (str): The user's email address.
            first_name (str, opcional): Optional user's first name. Defaults to None.
            last_name (str, opcional): Optional user's last name. Defaults to None.
            register (bool, opcional): Optional. If True, registers the user if they do not exist.
                Defaults to None.
            legal_terms_accepted (bool, opcional): Optional. Whether the user has accepted the
                legal terms. Defaults to None.

        Returns:
            Authentication: A model containing access and refresh tokens.

        Raises:
            InvalidEmailError: If the provided email format is invalid.
            MissingJwtSecretError: If the JWT secret is not configured in the client.
        """
        if re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", email) is None:
            raise InvalidEmailError()
        user_data = {
            k: v
            for k, v in {
                "username": email,
                "first_name": first_name,
                "last_name": last_name,
                "register": register,
                "legal_terms_accepted": legal_terms_accepted,
            }.items()
            if v is not None
        }

        secret = self._client.jwt_secret
        if not secret:
            raise MissingJwtSecretError()
        while len(secret) % 4 != 0:
            secret += "="
        dec = b64decode(secret)
        token = jwt.encode(user_data, dec, algorithm="HS256")

        return await self._client.http_request(
            method=Method.POST,
            path="login-jwt",
            model=Authentication,
            body={
                "client_id": self._client.client_id,
                "token": token,
            },
        )

    async def register(
        self,
        *,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        legal_terms_accepted: bool,
        jurisdiction_code: str | None = None,
    ) -> Authentication:
        """
        Registers a new user account and immediately authenticates the user.

        Use this tool to create a new user profile with the provided credentials
        and personal information. This action also logs the user in.

        Args:
            username (str): The email address to use as the username.
            password (str): The password for the new account.
            first_name (str): The user's first name.
            last_name (str): The user's last name.
            legal_terms_accepted (bool): Must be True to indicate acceptance of legal terms.
            jurisdiction_code (str, opcional): Optional jurisdiction code for the user.
                Defaults to None.

        Returns:
            Authentication: A model containing access and refresh tokens.

        Raises:
            MissingArgumentError: If any required argument (username, password,
                first_name, last_name) is missing.
        """
        if not username:
            raise MissingArgumentError("username")
        if not password:
            raise MissingArgumentError("password")
        if not first_name:
            raise MissingArgumentError("first_name")
        if not last_name:
            raise MissingArgumentError("last_name")

        return await self._client.http_request(
            method=Method.POST,
            path="login",
            model=Authentication,
            body={
                "client_id": self._client.client_id,
                "username": username,
                "password": password,
                "register": "true",
                "first_name": first_name,
                "last_name": last_name,
                "legal_terms_accepted": "true" if legal_terms_accepted else None,
                "jurisdiction_id": jurisdiction_code,
            },
        )

    async def login(
        self,
        *,
        username: str,
        password: str,
    ) -> Authentication:
        """
        Authenticates a user using their username (email) and password.

        Use this tool for standard user login to obtain access credentials.

        Args:
            username (str): The user's email address.
            password (str): The user's password.

        Returns:
            Authentication: A model containing access and refresh tokens.

        Raises:
            MissingArgumentError: If `username` or `password` is missing.
        """
        if not username:
            raise MissingArgumentError("username")
        if not password:
            raise MissingArgumentError("password")
        return await self._client.http_request(
            method=Method.POST,
            path="login",
            model=Authentication,
            body={
                "client_id": self._client.client_id,
                "username": username,
                "password": password,
            },
        )
