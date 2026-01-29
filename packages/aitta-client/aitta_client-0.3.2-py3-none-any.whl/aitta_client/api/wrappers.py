# SPDX-FileCopyrightText: 2025 CSC - IT Center for Science Oy
#
# SPDX-License-Identifier: MIT

from . import data_structures
from .data_structures import (
    ModelMetadata,
    SlurmResourcesRequired,
    SoftwareRequired,
    ModuleWorkerConfig,
    OllamaWorkerConfig,
    HuggingfaceWorkerConfig,
)
from typing import Any


class ModelBasicReference:
    """A (read-only) data container storing a model's id and root API endpoint."""

    def __init__(self, model_id: str, model_url_endpoint: str) -> None:
        self._id = model_id
        self._url = model_url_endpoint

    @property
    def id(self) -> str:
        return self._id

    @property
    def url_endpoint(self) -> str:
        return self._url

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, ModelBasicReference)
            and self.id == other.id
            and self._url == other._url
        )

    def __str__(self) -> str:
        return f"ModelReference({self.id} at {self.url_endpoint})"

    def __repr__(self) -> str:
        return str(self)


class ModelData(ModelBasicReference):
    """A (read-only) data container storing details about a model and its API interaction endpoints.

    Wrap in a `Model` instance to get an object that provides methods for performing model inference.
    """

    def __init__(self, api_response_data: data_structures.Model) -> None:
        self._data = api_response_data
        super().__init__(self._data.id, self._data.links.self.href)

    @property
    def infer_url_endpoint(self) -> str:
        return self._data.links.infer.href

    @property
    def description(self) -> str:
        return self._data.description

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ModelData) and self._data == other._data

    def __str__(self) -> str:
        return f"ModelData({self.id})"

    def __repr__(self) -> str:
        return str(self)


class TaskData:
    """A (read-only) data container storing details about an inference task and its API interaction endpoints.

    Wrap in a `Task` instance to get an object that provides methods for updating task status and results.
    """

    def __init__(self, api_response_data: data_structures.Task) -> None:
        self._data = api_response_data

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def url_endpoint(self) -> str:
        return self._data.links.self.href

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, TaskData) and self._data == other._data

    def __str__(self) -> str:
        return f"TaskData({self.id})"

    def __repr__(self) -> str:
        return str(self)


__all__ = [
    "ModelBasicReference",
    "ModelData",
    "TaskData",
    "ModelMetadata",
    "SlurmResourcesRequired",
    "SoftwareRequired",
    "ModuleWorkerConfig",
    "OllamaWorkerConfig",
    "HuggingfaceWorkerConfig",
]
