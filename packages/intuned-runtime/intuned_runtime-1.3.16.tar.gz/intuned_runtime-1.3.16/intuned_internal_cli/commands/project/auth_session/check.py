import json
import os
from typing import Any

import pydantic  # type: ignore
from more_termcolor import bold  # type: ignore
from more_termcolor import green  # type: ignore
from more_termcolor import red  # type: ignore
from tenacity import retry
from tenacity import retry_if_not_result
from tenacity import RetryError
from tenacity import stop_after_attempt

from _intuned_runtime_internal.context.context import IntunedContext
from _intuned_runtime_internal.errors.run_api_errors import RunApiError
from _intuned_runtime_internal.run.intuned_settings import load_intuned_settings
from _intuned_runtime_internal.run.run_api import import_function_from_api_dir
from _intuned_runtime_internal.run.run_api import run_api
from _intuned_runtime_internal.types.run_types import Auth
from _intuned_runtime_internal.types.run_types import AutomationFunction
from _intuned_runtime_internal.types.run_types import CDPRunOptions
from _intuned_runtime_internal.types.run_types import RunApiParameters
from _intuned_runtime_internal.types.run_types import StandaloneRunOptions
from _intuned_runtime_internal.types.run_types import StateSession
from _intuned_runtime_internal.types.run_types import StorageState
from _intuned_runtime_internal.types.run_types import TracingDisabled
from intuned_internal_cli.utils.wrapper import internal_cli_command


@internal_cli_command
async def project__auth_session__check(
    *,
    no_headless: bool = False,
    cdp_address: str | None = None,
    auth_session_path: str,
    auth_session_parameters: str | None = None,
):
    """
    Check the AuthSession.

    Args:
        cdp_address (str): The CDP address of the browser to load the AuthSession to.
        auth_session_path (str): Path to the AuthSession file.
        no_headless (bool): Whether to run the browser in headless mode.
        auth_session_parameters (str | None): JSON string with AuthSession parameters.
    """
    intuned_settings = await load_intuned_settings()
    if not intuned_settings.auth_sessions.enabled:
        raise Exception("AuthSessions are not enabled")

    if not os.path.exists(auth_session_path):
        raise Exception("AuthSession file does not exist")

    with open(auth_session_path) as f:
        try:
            auth_session = StorageState(**json.load(f))
        except (json.JSONDecodeError, TypeError) as e:
            raise Exception("AuthSession file is not a valid JSON file") from e
        except pydantic.ValidationError as e:
            raise Exception(f"AuthSession file is not valid: {e}") from e

    retry_configs = retry(stop=stop_after_attempt(2), retry=retry_if_not_result(lambda result: result is True))

    def import_function(file_path: str, function_name: str | None = None):
        return import_function_from_api_dir(
            file_path=file_path,
            automation_function_name=function_name,
            base_dir=os.path.join(os.getcwd()),
        )

    async def get_auth_session_parameters() -> dict[str, Any]:
        assert auth_session_parameters is not None
        try:
            return json.loads(auth_session_parameters)
        except json.JSONDecodeError as e:
            raise Exception("AuthSession parameters are not a valid JSON string") from e

    if auth_session_parameters is not None:
        IntunedContext.current().get_auth_session_parameters = get_auth_session_parameters

    try:

        async def check_fn():
            result = await run_api(
                RunApiParameters(
                    automation_function=AutomationFunction(
                        name="auth-sessions/check",
                        params=None,
                    ),
                    tracing=TracingDisabled(),
                    run_options=CDPRunOptions(
                        cdp_address=cdp_address,
                    )
                    if cdp_address is not None
                    else StandaloneRunOptions(headless=not no_headless),
                    auth=Auth(
                        session=StateSession(
                            state=auth_session,
                        ),
                    ),
                ),
                import_function=import_function,
            )
            check_result = result.result
            return check_result is True

        check_fn_with_retries = retry_configs(check_fn)
        try:
            result = await check_fn_with_retries()
        except RetryError:
            result = False
        success = type(result) is bool and result
        print(bold("Check result is"), bold(red(result)) if not success else bold(green(result)))
        if not success:
            raise Exception("AuthSession check failed")
    except RunApiError as e:
        raise Exception(f"Error running AuthSession check: {e}") from e
