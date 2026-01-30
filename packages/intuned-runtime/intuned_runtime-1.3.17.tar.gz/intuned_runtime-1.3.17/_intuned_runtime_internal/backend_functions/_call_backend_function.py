import json
from typing import Any
from typing import Literal

from httpx import AsyncClient
from pydantic import BaseModel

from _intuned_runtime_internal.constants import api_key_header_name
from _intuned_runtime_internal.context.context import IntunedContext
from _intuned_runtime_internal.env import get_api_key
from _intuned_runtime_internal.env import get_functions_domain
from _intuned_runtime_internal.env import get_is_running_in_cli
from _intuned_runtime_internal.env import get_project_id
from _intuned_runtime_internal.env import get_workspace_id


async def call_backend_function[T: BaseModel](
    name: str,
    validation_model: type[T],
    *,
    method: Literal["GET", "POST", "PUT"] = "GET",
    params: BaseModel | None = None,
) -> T:
    """
    Get the AuthSession parameters from the IntunedContext.
    """
    functions_domain, workspace_id, project_id = get_backend_functions_info()

    context = IntunedContext.current()

    async with AsyncClient() as client:
        api_key = get_api_key()
        if api_key is not None:
            client.headers[api_key_header_name] = api_key

        if context.functions_token:
            client.headers["Authorization"] = f"Bearer {context.functions_token}"
        if params:
            client.headers["Content-Type"] = "application/json"
        path = build_backend_functions_path(name, functions_domain, workspace_id, project_id)
        body = params.model_dump() if params else None

        response = await client.request(
            method,
            path,
            json=body,
        )
        try:
            response_json = response.json()
        except json.JSONDecodeError as e:
            raise CallBackendException(
                response.status_code,
                f"Expected JSON response, but got: {response.text}",
            ) from e
        if not isinstance(response_json, dict):
            raise CallBackendException(
                response.status_code,
                f"Expected JSON object, but got: {response_json}",
            )
        if 200 <= response.status_code < 300:
            return validation_model.model_validate(response_json)
        if response.status_code == 401 and get_is_running_in_cli():
            raise CallBackendException(
                response.status_code,
                "Unauthorized backend function call - make sure to provision your project to Intuned to set up the correct API credentials.\n"
                "Run 'intuned provision' or see https://docs.intunedhq.com/docs/05-references/cli#provision-project for more information.",
            )
        raise CallBackendException(
            response.status_code,
            f"Calling backend function errored with status {response.status_code}: {response_json}",
        )


def get_backend_functions_info():
    functions_domain, workspace_id, project_id = get_functions_domain(), get_workspace_id(), get_project_id()

    if functions_domain is None or workspace_id is None or project_id is None:
        if get_is_running_in_cli():
            raise Exception(
                "API credentials not set - make sure to provision your project to Intuned to set up the correct API credentials.\n"
                "Run 'intuned provision' or see https://docs.intunedhq.com/docs/05-references/cli#provision-project for more information."
            )

        raise Exception("No workspace ID or project ID found.")
    return functions_domain, workspace_id, project_id


def build_backend_functions_path(name: str, functions_domain: str, workspace_id: str, project_id: str):
    path = f"{functions_domain}/api/{workspace_id}/functions/{project_id}/{name}"
    return path


class CallBackendException(Exception):
    def __init__(self, status_code: int, body: str | dict[str, Any]):
        message = "Unknown error"
        if isinstance(body, str):
            message = body
        else:
            body_message = body.get("message") or body.get("error")
            if body_message:
                message = str(body_message)
            else:
                message = json.dumps(body)
        super().__init__(message)
        self.status_code = status_code
        self.body = body
