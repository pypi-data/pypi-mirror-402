<!--
SPDX-FileCopyrightText: 2024 CSC - IT Center for Science Oy

SPDX-License-Identifier: MIT
-->

# Python client for Aitta HPC ML inference platform

A Python client library for the Aitta ML inference platform for HPC systems.

> *__IMPORTANT__*: Note that both the API and the client library are still under heavy development and while
we try to keep changes mostly backwards-compatible, breaking changes may happen. Access to Aitta is
currently restricted to selected beta users.

## Main client API classes

### `AccessTokenSource`
Used by the client to get (and eventually refresh) access tokens

### `Client`
Implements all requests to the Aitta API servers on a low level and is used by all other classes.

Useful members:
- `get_model_list()`: Lists all models served by the API that can be accessed with the configured access credentials.

### `Model`
Represents a model and provides methods to perform inference.

Useful members:

- `load(model_id, client)`: Creates a Model instance given the models id, loading the relevant data from the Aitta API server.

### `Task`
Represents an active inference task and provides methods to query the current status and results.

Useful members:
- `max_progress`: The maximum number of progress increments of the task. Progress reporting is not supported by all models, in which case the return value is 1.
- `progress`: The current progress towards completion of the task. The increments are arbitrarily chosen by the model. Check max_progress for the maximum number of progress increments of the task.
If progress reporting is not supported by the model for this task the returned value is always 0 unless the task is successfully completed, in which case it is 1.
- `results`: The outputs of the model for inference request. Raises an IncompleteTaskError if the task was not yet 
  completed. Raises an InferenceError if the task was completed with a failure.

  
## Example usage

The below shows an example for usage of the Aitta API using the Python client library.

For accessing the Aitta API the client will need a way to obtain access tokens, which is
implemented in the form of an `AccessTokenSource`. For the time being, you can generate a static
model-specific token at the [web frontend](https://staging-aitta.2.rahtiapp.fi/) by opening
the model's page, switching to the "API Key" tab and pressing the "Generate API key" button.

With the token thus obtained, then have to create an instance of `StaticAccessTokenSource` for use
with the client library.

### Chat completion with the LumiOpen/Llama-Poro-2-70B-Instruct model
This example shows how to start a conversation with the model using OpenAI’s chat completion feature. 

> *__NOTE__*: It is recommended to specify the `max_tokens` value to a high enough number in order to avoid responses 
> being cut out.

```
from aitta_client import Model, Client, StaticAccessTokenSource
import openai

# configure Client instance with API URL and access token
access_token = "token_for_given_model"
token_source = StaticAccessTokenSource(access_token)
aitta_client = Client("https://api-staging-aitta.2.rahtiapp.fi", token_source)

# load the LumiOpen/Llama-Poro-2-70B-Instruct model
model = Model.load("LumiOpen/Llama-Poro-2-70B-Instruct", aitta_client)
print(model.description)

# configure OpenAI client to use the Aitta OpenAI compatibility endpoints
client = openai.OpenAI(api_key=token_source.get_access_token(), base_url=model.openai_api_url)
# perform chat completion with the OpenAI client
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Write a novel about bear talking about how to combine HPC with QC."
        }
    ],
    model=model.id,
    max_tokens=8000,
    stream=False  # response streaming is currently not supported by Aitta
)

print(chat_completion.choices[0].message.content)

```
