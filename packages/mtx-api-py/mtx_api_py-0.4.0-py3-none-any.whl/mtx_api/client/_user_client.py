from mtx_api.client._mtx_http_client import Method, MtxHttpClient
from mtx_api.models.auth import Gender, Profile
from mtx_api.models.base import EmptyResponse
from mtx_api.models.common import LegalTerms


class UserClient:
    def __init__(self, client: MtxHttpClient):
        self._client: MtxHttpClient = client

    async def profile(
        self,
        *,
        access_token: str | None = None,
    ) -> Profile:
        """Retrieves the profile information of the currently authenticated user.

        Use this tool to fetch details about the current user, including personal
        information and account settings.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.

        Returns:
            Profile: A model containing the user's profile details.
        """
        return await self._client.http_request(
            method=Method.GET,
            path="profile",
            model=Profile,
            access_token=access_token,
        )

    async def update_profile(
        self,
        *,
        access_token: str | None = None,
        email: str | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        twitter_nickname: str | None = None,
        phone: str | None = None,
        gender: Gender | None = None,
        birthday: str | None = None,
    ) -> Profile:
        """Updates the profile information of the currently authenticated user.

        Use this tool to modify the personal details and account information of
        the user. Only the fields provided will be updated; fields set to None
        will remain unchanged.

        Args:
            access_token: Optional token used for authentication. If not provided,
                the operation will be made without authentication.
            email: Optional new email address for the user.
            username: Optional new username for the user, typically their email address.
            first_name: Optional new first name or given name for the user.
            last_name: Optional new last name or family name for the user.
            twitter_nickname: Optional new shown name or twitter_nickname visible to others.
            phone: Optional new primary phone number for contact purposes.
            gender: Optional new gender identification for the user.
            birthday: Optional new date of birth in format YYYY-MM-DD.

        Returns:
            Profile: A model containing the updated user's profile details.
        """
        return await self._client.http_request(
            method=Method.PUT,
            path="profile",
            model=Profile,
            access_token=access_token,
            body={
                "email": email,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "twitterNickname": twitter_nickname,
                "phone": phone,
                "gender": gender,
                "birthday": birthday,
            },
        )

    async def accept_terms(
        self,
        *,
        access_token: str,
    ) -> bool:
        """Accepts the legal terms and conditions for the currently authenticated user.

        Use this tool to register the acceptance of legal terms for a previously
        registered user. Accepting these terms allows the user to use the platform.
        If not accepted, the user will not be allowed to use the platform.

        Should be used if a 451 error is received.

        Args:
            access_token: Optional token used for authentication. If not provided, the operation
                will be made without authentication.

        Returns:
            bool: True if the terms were successfully accepted.
        """
        await self._client.http_request(
            method=Method.POST,
            path="accept_terms",
            model=EmptyResponse,
            access_token=access_token,
        )
        return True

    async def legal_terms(
        self,
    ) -> LegalTerms:
        """
        Retrieves the current legal terms and conditions content.

        Use this function to fetch the complete legal terms and conditions content
        that users must accept to use the platform. The returned content may include
        plain text, formatted text, or links to external legal documents. This is
        typically given to users during registration or when terms have been
        updated and require re-acceptance.

        Returns:
            LegalTerms: A model containing the legal terms content, which may include
                privacy policy, terms of use, and cookies policy. Each field can
                contain text or links to legal documents.
        """
        return await self._client.http_request(
            method=Method.GET,
            path="legal-terms",
            model=LegalTerms,
        )
