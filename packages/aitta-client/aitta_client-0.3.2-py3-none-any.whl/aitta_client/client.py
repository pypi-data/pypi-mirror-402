# SPDX-FileCopyrightText: 2025 CSC - IT Center for Science Oy
#
# SPDX-License-Identifier: MIT

from typing import Iterable, Dict, Any
import pydantic
import pydantic_core
import requests
import time
from .api import data_structures
from .api.data_structures import ModelFromHubRequest
from .api.errors import handle_error_responses, MalformedAPIResponse, APIRateLimitError
from .api.wrappers import ModelBasicReference, ModelData, TaskData, ModelMetadata
from .authentication import AccessTokenSource


class Client:
    """Main API client implementation.

    Arguments:
        - url: The base URL of the API server, as a string.
        - access_token_source: An `AccessTokenSource` instances which provides an access token for API requests.
        - request_timeout_ms: The maximum waiting time for establishing a connection and receiving a response from the API.
        - retry_on_rate_limit_error: If True, upon receiving a rate limit error response from the API the client will automatically wait and reattempt the request.
    """

    def __init__(
        self,
        url: str,
        access_token_source: AccessTokenSource,
        request_timeout_ms: int = 1000,
        retry_on_rate_limit_error: bool = False,
    ) -> None:
        self._url = url

        self._token_source = access_token_source
        self._timeout_ms = request_timeout_ms
        self._retry_on_rate_limit_error = retry_on_rate_limit_error

    @property
    def access_token_source(self) -> AccessTokenSource:
        return self._token_source

    def _endpoint_to_url(self, endpoint: str | data_structures.Link) -> str:
        if isinstance(endpoint, data_structures.Link):
            endpoint = endpoint.href

        return self._url + endpoint

    def _make_request_headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": "Bearer " + self.access_token_source.get_access_token()
        }
        return headers

    def _make_request(
        self,
        endpoint: str | data_structures.Link,
        json: dict[str, Any] | pydantic.BaseModel = None,
        method: str | None = None,
    ) -> requests.Response:
        if method is None:
            if json is not None:
                method = "POST"
            else:
                method = "GET"

        if isinstance(json, pydantic.BaseModel):
            json = pydantic_core.to_jsonable_python(json)

        headers = self._make_request_headers()
        url = self._endpoint_to_url(endpoint)

        while True:
            try:
                response = requests.request(
                    method, url, headers=headers, timeout=self._timeout_ms, json=json
                )
                handle_error_responses(response)
                return response
            except APIRateLimitError as e:
                if self._retry_on_rate_limit_error:
                    time.sleep(e.retry_after)
                else:
                    raise

    def _parse_model_response(self, response: requests.Response) -> ModelData:
        try:
            model_data = data_structures.Model.model_validate_json(response.content)
            return ModelData(model_data)
        except pydantic.ValidationError as e:
            raise MalformedAPIResponse(
                "The API server response could not be parsed."
            ) from e

    def get_model_list(self) -> Iterable[ModelBasicReference]:
        """Lists all models served by the API that can be accessed with the configured access credentials.

        Returns:
            an iterable collection of models represented as `ModelBasicReference` instances, consiting of the model name/id and their main API endpoints
        """
        response = self._make_request("/model")

        try:
            model_list = data_structures.ModelList.model_validate_json(response.content)
            return [
                ModelBasicReference(model_link.name, model_link.href)
                for model_link in model_list.links.item
            ]
        except pydantic.ValidationError as e:
            raise MalformedAPIResponse(
                "The API server response could not be parsed."
            ) from e

    def get_model(self, model_reference: ModelBasicReference) -> ModelData:
        """Retrieves detailed information about a model.

        Arguments:
            - model_reference: A `ModelBasicReference` instance representing the API endpoints of the model for which detailed information shall be retrieved.

        Returns:
            detailed information of the model as a `ModelData` object
        """
        return self._parse_model_response(
            self._make_request(model_reference.url_endpoint)
        )

    def get_model_metadata(self, model: ModelData) -> ModelMetadata:
        """Retrieves the metadata of the model as stored in the Aitta model repository.

        It is recommended to use `Model.get_metadata` for convenience.

        Arguments:
            - model: A `ModelData` instance representing the model for which metadata shall be retrieved.

        Returns:
            model metadata as a `ModelMetadata` object

        Raises:
            - `UnavailableFeatureError` if metadata is not available, e.g., due to lacking access permissions
        """

        if not model._data.links.metadata:
            raise UnavailableFeatureError("model metadata")

        response = self._make_request(model._data.links.metadata)

        try:
            model_metadata = data_structures.ModelMetadata.model_validate_json(
                response.content
            )
            return model_metadata
        except pydantic.ValidationError as e:
            raise MalformedAPIResponse(
                "The API server response could not be parsed."
            ) from e

    def update_model_metadata(
        self, model: ModelBasicReference, model_metadata: ModelMetadata
    ) -> None:
        """Updates the model's metadata in the Aitta model repository.

        It is recommended to use `Model.update_metadata` for convenience.

        Arguments:
            - model: A `ModelBasicReference` instance representing the model for which metadata shall be updated.
            - metadata: The complete new `ModelMetadata` data structure with which to overwrite the existing data in the model repository.
        """
        self._make_request(
            model.url_endpoint,
            json=model_metadata,
            method="PUT",
        )

    def add_model(self, model_metadata: ModelMetadata) -> ModelData:
        """Adds a new model to the Aitta model repository with the given metadata.

        At this point currently no checks are performed that the model configuration is valid and will run successfully.
        Note that the model parameters/weights are downloaded only upon first use, which may cause long delays for the first request to the model
        or failure.

        It is recommended to fetch and adapt the metadata structure of a similar model for best chance at success.

        Currently only Aitta administrators have the required permission to add new models.

        Arguments:
            - metadata: The complete `ModelMetadata` data structure for the new model to add to the model repository.
        """
        return self._parse_model_response(
            self._make_request("/model", json=model_metadata)
        )

    def add_model_from_huggingface(
        self, modelhubrequest: ModelFromHubRequest
    ) -> ModelData:
        """Adds a new model to the Aitta model repository from huggingface.

        At this point currently LLMs and Sentence Embedding models are only supported. Also there are limitations for models that need some kind of authentication.

        Currently only Aitta administrators have the required permission to add new models.

        Arguments:
            - model_id: The ID of the model to add, as it is in huggingface. E.g. 'LumiOpen/Llama-Poro-2-70B-Instruct'
            - owner: The owner of the model. E.g. 'public'
            - scopes: A set of scopes that are set for the model. E.g. "['public', 'projectx']"
        """
        return self._parse_model_response(
            self._make_request("/model/huggingface", json=modelhubrequest)
        )

    def start_inference(
        self, model: ModelData, inputs: Dict[str, Any], params: Dict[str, Any]
    ) -> TaskData:
        """Starts a model inference task for the given model.

        This is a low-level implementation of API requests. You probably want to use `Model.start_inference` instead.

        This method does not block until the inference task is completed. Use the `get_task` method
        with the returned `TaskData` object to fetch updated progress information and results of the task.

        Does not currently perform any input processing or validation.

        Arguments:
            - model: A `ModelData` instance of the model with which to perform inference.
            - inputs: A dictionary of (batched) inputs to the model for the inference task.
                    See the model description in the `ModelData` instance of the model for details on accepted inputs and formats.
            - params: A dictionary of parameters that affect the model's behaviour during inference.
                    See the model description in the `ModelData` instance of the model for details on accepted parameters.

        Returns:
            a `TaskData` object containing details about the inference task and its API interaction endpoints.
        """
        response = self._make_request(
            model.infer_url_endpoint, json={**inputs, **params}
        )

        try:
            task_data = data_structures.Task.model_validate_json(response.content)
            return TaskData(task_data)
        except pydantic.ValidationError as e:
            raise MalformedAPIResponse(
                "The API server response could not be parsed."
            ) from e

    def get_task(self, task: TaskData) -> TaskData:
        """Obtain updated model inference task data.

        This is a low-level implementation of API requests. You probably want to use `Task.update` instead.

        Arguments:
            - task: A `TaskData` instance of the task for which to fetch updated information from the API.

        Returns:
            a `TaskData` instance containing current information about the task
        """
        response = self._make_request(task.url_endpoint)

        try:
            task_data = data_structures.Task.model_validate_json(response.content)
            return TaskData(task_data)
        except pydantic.ValidationError as e:
            raise MalformedAPIResponse(
                "The API server response could not be parsed."
            ) from e


class UnavailableFeatureError(Exception):

    def __init__(self, feature_name: str) -> None:
        super().__init__(
            f"'{feature_name.capitalize()}' is currently not available. "
            f"You may be lacking the necessary permissions."
        )


__all__ = ["Client", "UnavailableFeatureError"]
