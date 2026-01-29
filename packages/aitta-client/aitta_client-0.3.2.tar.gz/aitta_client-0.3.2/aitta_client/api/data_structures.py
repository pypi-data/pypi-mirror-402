# SPDX-FileCopyrightText: 2025 CSC - IT Center for Science Oy
#
# SPDX-License-Identifier: MIT

from pydantic import BaseModel, Field
import enum
from typing import List, Dict, Any, Optional, Set


class TaskState(str, enum.Enum):
    Pending = "Pending"
    Running = "Running"
    Success = "Success"
    Failure = "Failure"


class HTTPMethod(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    DELETE = "DELETE"
    PUT = "PUT"
    PATCH = "PATCH"


class Link(BaseModel):
    """A hypertext application language link object, linking one resource to another."""

    href: str = Field(description="The URI of the linked resource.")
    name: str | None = Field(
        default=None,
        description="A unique name for the linked resource from the perspective of the linking resource.",
    )
    title: str | None = Field(
        default=None, description="A human-readable label for the link."
    )
    method: HTTPMethod = Field(
        default=HTTPMethod.GET, description="The HTTP method to use with the link."
    )

    model_config = {"frozen": True}


class ModelLinks(BaseModel):
    self: Link
    infer: Link
    collection: Link
    openai_chat_completion: Optional[Link] = Field(None, alias="openai-chat-completion")
    openai_embeddings: Optional[Link] = Field(None, alias="openai-embeddings")
    openai: Optional[Link] = None
    metadata: Optional[Link] = None


class Model(BaseModel):
    """Detailed information about a model served by the API.

    NOTE(2023-11-15): Since the API is still in development, details about inputs and outputs for models are not yet available via the API in a parseable manner.
    """

    id: str = Field(description="A unique identifier for the model.")
    description: str = Field(
        description="A human-readable description of the model and expected inputs and outputs."
    )
    capabilities: set[str] = Field(description="A set of capabilities of the model.")
    links: ModelLinks = Field(
        alias="_links",
        description="Links to interact with the resource and obtain information about related resources.",
    )


class ModelListLinks(BaseModel):
    self: Link
    item: List[Link]


class ModelList(BaseModel):
    """A list of models served by the API with URIs from which more information for each model can be obtained.

    The following links are provided:
    - self: Refer back to the resource itself.
    - item: Obtain information about any particular model in the list.
    """

    links: ModelListLinks = Field(
        alias="_links",
        description="Links to interact with the resource and obtain information about related resources.",
    )


class HuggingfaceWorkerConfig(BaseModel):
    """Worker configuration for a model from huggingface hub run with transformers library code."""

    model_path: str
    worker_class: str
    loading_arguments: Dict[str, Any] | None = None
    chat_template: str | None = None


class ModuleWorkerConfig(BaseModel):
    """Worker configuration for a model run from a custom implementation provided as a python module.

    The module must set up and export an instance of class `ModelInferenceWorker`.
    E.g., if the worker module is located in "worker/my_worker.py" and sets up a worker instance called "my_worker_obj",
    the configuration should be `module_path=api.worker.my_worker` and `worker_object_name=my_worker_obj`.
    """

    module_path: str
    worker_object_name: str


class OllamaWorkerConfig(BaseModel):
    """Worker configuration for a model run via Ollama server process."""

    ollama_model_name: str


class VllmWorkerConfig(BaseModel):
    """Worker configuration for a model from huggingface hub run with vllm library code."""

    model_path: str
    concurrency: int = 1
    loading_arguments: Dict[str, Any] | None = None


class SlurmResourcesRequired(BaseModel):
    """Lists the resources that have to be allocated to run the model in a particular SLURM cluster."""

    ram_mb: int
    num_gpus: int
    num_cpus: int


class SoftwareRequired(BaseModel):
    """Settings for selecting the software with which to run the model.

    Currently only in use for Ollama based models, as HuggingFace based one use a default module on LUMI at the moment (but this will change in the future).
    """

    container_path: str | None = None


class ModelMetadata(BaseModel):
    """Metadata for a model.

    The metadata controls how the model is run and what inputs are accepted by the Aitta API.
    """

    id: str = Field(
        description="A unique id of the model, of the form <publisher>/<model_name>."
    )
    description: str = Field(
        description="A textual description of the model, its intended usage and limitations for the user."
    )
    capabilities: set[str] = Field(
        description="A set of capability keywords that indicate e.g. whether the model can be used for OpenAI chat completion or embeddings."
    )
    worker_config: (
        HuggingfaceWorkerConfig
        | ModuleWorkerConfig
        | OllamaWorkerConfig
        | VllmWorkerConfig
    ) = Field(
        description="Configuration options for sourcing the actual model parameters, depending on the type of model worker."
    )
    resources: SlurmResourcesRequired = Field(
        description="The resources (memory, number of GPUs) that need to be allocated to run the model."
    )
    software: SoftwareRequired = Field(
        description="Configuration options for software dependencies that must be loaded in order to run the model."
    )
    inputs: dict[str, Any] = Field(
        description="A mapping of input keys to expected types and shapes, used to validate inputs before they are processed by the model."
    )
    outputs: dict[str, Any] = Field(
        description="A mapping of output keys to types and shapes."
    )
    parameters: dict[str, Any] = Field(
        description="A mapping of parameter keys to expected types. Parameters allow to control some aspects of the model's behaviour while processing inputs."
    )
    supports_batching: bool = Field(
        description="Whether or not the model supports processing batches of inputs via the default inference endpoint /model/<model_id>/task ."
    )
    scopes: set[str] = Field(
        description="A set of access scopes, indicating which users have access to the model."
    )
    owner: str = Field(
        description="The owning scope of the model. Users in this scope can change or delete model metadata."
    )


class TaskProgress(BaseModel):
    progress: int = Field(
        description="Processing progress of the inference request. Each increment corresponds to an unspecified amount of progress. The total number of increments (maximum value of progress) is available from the total_progress field, if known.",
        ge=0,
    )
    total_progress: int | None = Field(
        description="The total number of progress increments, i.e., maximum value of the progress field. May be None, which indicates that the total number of increments is unknown.",
        gt=0,
    )


class TaskLinks(BaseModel):
    self: Link
    stop: Link
    model: Link


class Task(BaseModel):
    """Information about an ongoing or completed inference task.

    The following links are provided:
    - self: Refer back to the resource itself.
    - stop: Revoke an inference request that is pending execution.
    - model: Obtain information about the model serving this task.
    """

    id: str = Field(description="A unique identifier for the task.")
    model_id: str = Field(
        description="The unique identifier of the model to which the inference request is made."
    )
    state: TaskState = Field(
        description="The current state of the task, i.e., whether it is pending execution, currently being executed, completed or failed."
    )
    error: Any | None = Field(
        description="Contains further information about an encountered error if the task completed with a failure."
    )
    results: Any | None = Field(
        description="Contains the result of the inference task if the task completed successfully."
    )
    progress: TaskProgress | None = Field(
        description="Information on the current progress of the task. Only set if `state` is `Running` and if progress information is available for the task/model."
    )
    links: TaskLinks = Field(
        alias="_links",
        description="Links to interact with the resource and obtain information about related resources.",
    )

    model_config = {"protected_namespaces": ()}


class APIError(BaseModel):
    error: str
    error_description: str | None = Field(
        default=None, description="Human-readable text providing additional information"
    )
    error_uri: str | None = Field(
        default=None,
        description="A URI identifying a human-readable web page with information about the error, used to provide the user with additional information about the error.",
    )
    details: Dict[str, Any] | None = Field(
        default=None,
        description="A JSON object containing further information on the cause of the error, if applicable.",
    )


class AccessToken(BaseModel):
    """The response for an access token request. Follows in large parts the OAuth2 reponse format (https://datatracker.ietf.org/doc/html/rfc6749#section-5.1) but excludes scope information."""

    access_token: str = Field(
        description="The access token that must be provided as HTTP bearer token to all API calls."
    )
    expires_in: int = Field(
        description="The remaining lifetime of the token (in seconds), after which it can no longer be used."
    )
    token_type: str = Field(
        default="Bearer",
        description="The type of the token issued as described in the OAuth2 specification. Always 'Bearer'.",
    )
    refresh_token: str | None = Field(
        default=None,
        description="An optional refresh token, which can be used to obtain new access tokens if provided.",
    )


class ModelFromHubRequest(BaseModel):
    model_id: str = Field(
        ..., description="Hugging Face model identifier, e.g. 'openai-community/gpt2'"
    )
    owner: str = Field(
        ..., description="Owner for the model in your repo, e.g. 'public'"
    )
    scopes: Set[str] = Field(
        default_factory=set, description="Scopes e.g '[public, projectX]'"
    )
