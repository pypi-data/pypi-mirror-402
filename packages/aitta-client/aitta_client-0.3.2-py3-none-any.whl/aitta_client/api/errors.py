# SPDX-FileCopyrightText: 2024 CSC - IT Center for Science Oy
#
# SPDX-License-Identifier: MIT

from typing import Dict, Any
import requests
import pydantic
from . import data_structures


class APIError(Exception):
    pass


class MalformedAPIResponse(APIError):
    pass


class APIErrorResponse(APIError):

    def __init__(self, error_data: data_structures.APIError) -> None:
        self._data = error_data
        super().__init__(
            f"The API responded with error '{self.error_type}': {self.error_description}"
        )

    @property
    def error_type(self) -> str:
        return self._data.error

    @property
    def error_description(self) -> str:
        return self._data.error_description

    @property
    def details(self) -> Dict[str, Any]:
        return self._data.details


class AuthorizationError(APIErrorResponse):
    pass


class ServiceUnderMaintenanceError(APIErrorResponse):
    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} (details={self.details})"


class APIRateLimitError(APIErrorResponse):
    """In APIRateLimitError exceptions the retry_after specifies the time to wait in seconds."""

    def __init__(self, error_data, retry_after: int | None = None):
        super().__init__(error_data)
        self._retry_after = retry_after

    @property
    def retry_after(self) -> int:
        """The time to wait (in seconds) specified by the server."""
        return self._retry_after


def handle_error_responses(
    response: requests.Response, content_type: str = "application/hal+json"
) -> None:
    """Parses error responses from the API and translates them into exceptions."""
    if not response.ok:
        try:
            error_data = data_structures.APIError.model_validate_json(response.content)
            if response.status_code == 401:
                raise AuthorizationError(error_data)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                raise APIRateLimitError(error_data, retry_after)
            if response.status_code == 503:
                raise ServiceUnderMaintenanceError(error_data)
            raise APIErrorResponse(error_data)
        except pydantic.ValidationError as e:
            if response.status_code == 500:
                raise APIError(
                    "The API encountered an internal error and did not provide a response."
                )
            raise MalformedAPIResponse(
                "The API server responded with an error response, but it could not be parsed."
            ) from e

    if "content-type" not in response.headers:
        raise MalformedAPIResponse(
            "The API server response did not provide a content type header."
        )
    elif response.headers["content-type"] != content_type:
        raise MalformedAPIResponse(
            f"The API server response did not have the expected content type. Expected '{content_type}' but got '{response.headers['content-type']}'."
        )
