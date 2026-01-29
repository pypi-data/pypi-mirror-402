# SPDX-FileCopyrightText: 2024 CSC - IT Center for Science Oy
#
# SPDX-License-Identifier: MIT

import abc
import jwt as pyjwt
import pydantic
import datetime
import warnings
import requests
from .api.errors import MalformedAPIResponse, handle_error_responses
from .api import data_structures


class AccessTokenExpired(Exception):

    def __init__(self, expiration_time: datetime.datetime) -> None:
        super().__init__(f"The access token has expired at {expiration_time}")


class AccessTokenWillExpire(Warning):
    pass


class AccessTokenSource(metaclass=abc.ABCMeta):
    """Provides API access tokens to `Client` instances."""

    @abc.abstractmethod
    def get_access_token(self) -> str:
        pass


class JSONWebTokenClaims(pydantic.BaseModel):
    exp: datetime.datetime


class StaticAccessTokenSource(AccessTokenSource):
    """Provides a statically configured access token.

    Arguments:
        - access_token: A static access token obtained from the Aitta web frontend.
    """

    def __init__(self, access_token: str) -> None:
        self._access_token = access_token
        self._warn_if_token_expires(
            access_token, expiry_threshold=datetime.timedelta(weeks=3)
        )

    @staticmethod
    def _warn_if_token_expires(
        access_token: str, expiry_threshold: datetime.timedelta
    ) -> None:
        try:
            unverified_claims = pyjwt.decode(
                access_token, key=None, options={"verify_signature": False}
            )

            unverified_claims = JSONWebTokenClaims.model_validate(unverified_claims)

            now = datetime.datetime.now().astimezone(tz=datetime.timezone.utc)
            if now >= unverified_claims.exp:
                raise AccessTokenExpired(unverified_claims.exp)

            if now + expiry_threshold >= unverified_claims.exp:
                warnings.warn(
                    f"Your access token will expire at {unverified_claims.exp}.",
                    AccessTokenWillExpire,
                )

        # if we cannot read the token, we assume its an error on our part and allow the user to use the token; if it's not valid, the API will reject it and let the user know
        except pyjwt.exceptions.DecodeError:
            pass
        except pydantic.ValidationError:
            pass

    def get_access_token(self) -> str:
        return self._access_token


class APIKeyAccessTokenSource(AccessTokenSource):
    """Provides access tokens obtained using a given API key.

    Arguments:
        - api_key: A static API key.
    """

    def __init__(self, api_key: str, api_url: str) -> None:
        self._url = api_url
        self._api_key = api_key
        self._current_token: str | None = None
        self._token_expires: datetime.datetime | None = None

    def _fetch_token_if_required(self) -> str:
        now = datetime.datetime.now().astimezone(tz=datetime.timezone.utc)
        if self._token_expires is None or self._token_expires < now:
            headers = {"Authorization": "Bearer " + self._api_key}
            response = requests.request(
                "GET", self._url + "/authenticate_with_key", headers=headers
            )
            handle_error_responses(response, "application/json")

            try:
                access_token_response = data_structures.AccessToken.model_validate_json(
                    response.content
                )
                self._current_token = access_token_response.access_token
                expires_in = datetime.timedelta(
                    seconds=access_token_response.expires_in
                ) - datetime.timedelta(seconds=5)
                self._token_expires = now + expires_in
            except pydantic.ValidationError as e:
                raise MalformedAPIResponse(
                    "The API server response could not be parsed."
                ) from e

    def get_access_token(self) -> str:
        self._fetch_token_if_required()
        assert self._current_token is not None

        return self._current_token


__all__ = [
    "AccessTokenSource",
    "StaticAccessTokenSource",
    "APIKeyAccessTokenSource",
    "AccessTokenExpired",
    "AccessTokenWillExpire",
]
