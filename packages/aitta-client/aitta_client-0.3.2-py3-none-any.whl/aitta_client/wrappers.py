# SPDX-FileCopyrightText: 2025 CSC - IT Center for Science Oy
#
# SPDX-License-Identifier: MIT

from typing import Dict, Any, Optional
import requests
from .api.data_structures import TaskState
from .api import wrappers, errors
from . import client
import time


class Model(wrappers.ModelData):
    """Represents a machine learning model served by Aitta.

    Obtain a `Model` object by wrapping the result of `Client.get_model` or by using `Model.load`.

    Arguments:
        - model_data: An `api.wrappers.ModelData` instance containing information about the model.
        - client: A `Client` object used for making requests to the API server.
    """

    def __init__(self, model_data: wrappers.ModelData, client: client.Client) -> None:
        super().__init__(model_data._data)
        self._client = client
        self._metadata: None | wrappers.ModelMetadata = None

    def __str__(self) -> str:
        return f"Model({self.id})"

    @staticmethod
    def load(
        model_id: str | wrappers.ModelBasicReference, client: client.Client
    ) -> "Model":
        """Creates a Model instance given the models id, loading the relevant data from the Aitta API server.

        Arguments:
            - model_id: The unique identifier or a `ModelBasicReference` instance identifying the model.
            - client: A `Client` object used for making requests to the API server.

        Returns:
            a `Model` instance for the model with the given `model_id`
        """
        if isinstance(model_id, wrappers.ModelBasicReference):
            model_reference = model_id
        else:
            model_references = [m for m in client.get_model_list() if m.id == model_id]
            if not model_references:
                raise ModelNotFoundError(model_id)

            model_reference = model_references[0]

        model_data = client.get_model(model_reference)

        return Model(model_data, client)

    def start_inference(self, inputs: Dict[str, Any], params: Dict[str, Any]) -> "Task":
        """Makes a request to the API server to start an inference task and returns a `Task` object.

        Does not wait for the inference to finish. You will need to manually update the returned `Task`
        and check its state to determine if the inference was completed.

        Does not currently perform any input processing or validation.

        Arguments:
            - inputs: Inputs to the model. Check the model description to determine the names (keys) of model inputs and a description of type and format
                of the data accepted by the model. Values must be either JSON serializable or (lists of) `bytes` objects.
            - params: Infernece parameters for the model. Check the model description to determine the names (keys) of parameters.

        Returns:
            a `Task` object for the started inference task with which results and progress can be checked.
        """

        return Task(self._client.start_inference(self, inputs, params), self)

    def start_and_await_inference(
        self,
        inputs: Dict[str, Any],
        params: Dict[str, Any],
        timeout_ms: int | None = None,
        polling_interval_ms: int = 500,
    ) -> Any:
        """Makes a request to the API server to start and inference task and waits for and returns the result.

        Does not currently perform any input processing or validation.

        Arguments:
            - inputs: Inputs to the model. Check the model description to determine the names (keys) of model inputs and a description of type and format
                of the data accepted by the model. Values must be either JSON serializable or (lists of) `bytes` objects.
            - params: Inference parameters for the model. Check the model description to determine the names (keys) of parameters.
            - timeout_ms: An optional maximum time to wait for the inference task to complete, in milliseconds. No maximum time if left as `None`.
            - polling_interval_ms: The time interval to wait before polling the API server for updates on the task, in milliseconds.

        Returns:
            the response produced by the model for the given inputs.
        """
        polling_interval_secs = polling_interval_ms / 1000
        end_time = (time.time() + timeout_ms / 1000) if timeout_ms is not None else None

        task = self.start_inference(inputs, params)
        while not task.completed:
            try:
                time.sleep(polling_interval_secs)
                task.update()
            except errors.APIRateLimitError as e:
                time.sleep(max(e.retry_after - polling_interval_secs, 0))

            if end_time is not None and time.time() < end_time:
                raise requests.Timeout()

        return task.results

    @property
    def openai_api_url(self) -> Optional[str]:
        """Returns the OpenAI API endpoint URL if the specified model is compatible with the OpenAI platform.

        The model is compatible if `model_capabilities` contains the `openai-chat-completion` capability.

        If the model is not compatible, an `IncompatibleModelError` is raised instead.

        Returns:
            the OpenAI API endpoint URL is returned as a string.
        """
        links = self._data.links
        if links.openai:
            url = links.openai.href
            if url.startswith("/"):
                url = self._client._endpoint_to_url(url)
            return url
        else:
            raise IncompatibleModelError(self.id)

    @property
    def model_capabilities(self) -> set[str]:
        """Returns the model capabilities.

        Returns:
            the model capabilities as a set of keywords. Empty if there are no special capabilities.
        """
        capabilities = self._data.capabilities.copy()
        return capabilities

    def get_metadata(self, ignore_cached: bool = False) -> wrappers.ModelMetadata:
        """Fetches and returns the model metadata.

        Model metadata is the information stored about the model in the Aitta database. This includes
        the common model information like the description, inputs, outputs and parameters as well as
        configuration options required to run the model on Aitta hardware, e.g., the number of GPUs
        that must be allocated and what software components to load.

        To prevent repeated queries to the server, this method caches the obtained metadata and
        on subsequent calls returns the cached result. Set the `ignore_cached` argument to `True`
        to enforce fetching the data from the Aitta API again.

        Arguments:
            - ignore_cached: If True, cached responses from previous calls are ignored and the
                data is retrieved from the server.

        Returns:
            a `ModelMetadata` object containing the model's metadata as stored in the database.

        Raises:
            - `UnavailableFeatureError` if metadata is not available, e.g., due to lacking access permissions
        """
        if ignore_cached or self._metadata is None:
            self._metadata = self._client.get_model_metadata(self)
        return self._metadata.model_copy()

    def update_metadata(self, metadata: wrappers.ModelMetadata) -> None:
        """Updates the model's metadata in the Aitta model repository.

        Model metadata is the information stored about the model in the Aitta database. This includes
        the common model information like the description, inputs, outputs and parameters as well as
        configuration options required to run the model on Aitta hardware, e.g., the number of GPUs
        that must be allocated and what software components to load.

        Arguments:
            - metadata: The complete new `ModelMetadata` data structure with which to overwrite the existing data in the model repository.
        """
        self._client.update_model_metadata(self, metadata)
        self._metadata = metadata


class Task(wrappers.TaskData):
    """Represents a model inference task performed by aitta.

    Tasks can be ongoing or complete, either successfully or with a failure. Check the `state` property to determine the tasks last known state.

    Arguments:
        - task_data: An `api.wrappers.TaskData` instance containing information about the task from an API response.
        - model: A `Model` instance representing the model performing the inference task.
    """

    def __init__(self, task_data: wrappers.TaskData, model: Model) -> None:
        super().__init__(task_data._data)
        if model.id != task_data._data.model_id:
            raise ValueError(
                f"The provided model '{model.id}' does not match the one associated with the task: '{task_data._data.model_id}'."
            )
        self._model = model

    @property
    def state(self) -> TaskState:
        return self._data.state

    @property
    def results(self) -> Any:
        """The outputs of the model for inference request.

        Raises an `IncompleteTaskError` if the task was not yet completed.
        Raises an `InferenceError` if the task was completed with a failure.
        """
        if not self.completed:
            raise IncompleteTaskError(self)

        if self.state == TaskState.Failure:
            raise InferenceError(self, self._data.error)

        return self._data.results

    @property
    def completed(self) -> bool:
        return self.state in (TaskState.Failure, TaskState.Success)

    @property
    def progress(self) -> int:
        """The current progress towards completion of the task.

        The increments are arbitrarily chosen by the model. Check `max_progress` for
        the maximum number of progress increments of the task.

        If progress reporting is not supported by the model for this task
        the returned value is always `0` unless the task is successfully completed,
        in which case it is `1`.
        """
        if self._data.progress is None:
            if self.state == TaskState.Success:
                return 1
            else:
                return 0
        return self._data.progress.progress

    @property
    def max_progress(self) -> int:
        """The maximum number of progress increments of the task.

        Progress reporting is not supported by all models, in which case
        the return value is `1`.
        """
        if self._data.progress is None or self._data.progress.total_progress is None:
            return 1
        return self._data.progress.total_progress

    def update(self) -> None:
        """Makes a query to the API to update the task information."""
        new_task = self._model._client.get_task(self)
        self._data = new_task._data

    def __str__(self) -> str:
        return f"Task({self.id})"


class ModelNotFoundError(Exception):

    def __init__(self, model_id: str) -> None:
        super().__init__(f"The model '{model_id}' is not available.")
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id


class IncompleteTaskError(Exception):

    def __init__(self, task: Task) -> None:
        super().__init__(
            f"The inference task {task.id} has not completed yet; current state is {task.state}"
        )
        self._task = task

    @property
    def task(self) -> Task:
        return self._task


class InferenceError(Exception):

    def __init__(self, task: Task, details: Any) -> None:
        super().__init__(
            f"The inference task {task.id} encountered an error during processing."
        )
        self._task = task
        self._details = details

    @property
    def details(self) -> Any:
        return self._details

    @property
    def task(self) -> Task:
        return self._task


class IncompatibleModelError(Exception):

    def __init__(self, model_id: str) -> None:
        super().__init__(
            f"The model '{model_id}' is not compatible with the OpenAI API."
            f"No OpenAI chat completion link found in the model's metadata."
        )
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id
