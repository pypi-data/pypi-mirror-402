import json
from typing import Any
from typing import Literal

from anyio import Path

from _intuned_runtime_internal.types.settings_types import IntunedJsonEnabledAuthSessions
from intuned_cli.utils.api_helpers import get_intuned_settings_file_name
from intuned_cli.utils.api_helpers import load_intuned_json
from intuned_cli.utils.error import CLIError


class CLIAssertionError(CLIError):
    pass


async def is_auth_enabled() -> bool:
    intuned_json = await load_intuned_json()
    return intuned_json.auth_sessions.enabled


async def assert_auth_enabled(*, auth_type: Literal["API", "MANUAL"] | None = None):
    if not await is_auth_enabled():
        raise CLIAssertionError(
            f"AuthSessions are not enabled.\n"
            f"Enable AuthSessions in {await get_intuned_settings_file_name()} to use this feature.\n"
            f"See https://docs.intunedhq.com/docs/cli/auth-sessions for more information."
        )
    if auth_type is None:
        return
    intuned_json = await load_intuned_json()
    if (
        type(intuned_json.auth_sessions) is IntunedJsonEnabledAuthSessions
        and intuned_json.auth_sessions.type != auth_type
    ):
        if auth_type == "API":
            raise CLIAssertionError(
                f"AuthSession type is not credentials-based in {await get_intuned_settings_file_name()}. Set it to 'API' to run this command."
            )

        raise CLIAssertionError(
            f"AuthSession type is not recorder-based in {await get_intuned_settings_file_name()}. Set it to 'MANUAL' to run this command."
        )


async def assert_auth_consistent(auth_session_id: str | None = None):
    _is_auth_enabled = await is_auth_enabled()
    if _is_auth_enabled and auth_session_id is None:
        raise CLIAssertionError(
            "AuthSessions are enabled but no AuthSession was provided.\n"
            "Please provide --auth-session <id>.\n"
            "See https://docs.intunedhq.com/docs/cli/auth-sessions for more information."
        )
    if not _is_auth_enabled and auth_session_id is not None:
        raise CLIAssertionError(
            f"AuthSession is not enabled, enable it in {await get_intuned_settings_file_name()} to use it"
        )


async def load_parameters(parameters: str) -> dict[str, Any]:
    """
    Load parameters from a JSON file or a JSON string.
    If the input is a file path, it reads the file and returns the parsed JSON.
    If the input is a JSON string, it parses and returns the JSON.
    """

    try:
        # Check if the input is a file path
        path = Path(parameters)
        if await path.exists():
            content = await path.read_text()
            return json.loads(content)
        else:
            # If not a file, treat it as a JSON string
            return json.loads(parameters)
    except json.JSONDecodeError as e:
        raise CLIError(f"Parameters have invalid JSON format: {e}") from e
    except Exception as e:
        raise CLIError(f"Failed to load parameters: {e}") from e


async def get_auth_session_recorder_parameters() -> tuple[str, str]:
    intuned_json = await load_intuned_json()
    auth_session_settings = intuned_json.auth_sessions
    if type(auth_session_settings) is not IntunedJsonEnabledAuthSessions:
        raise CLIError(
            f"AuthSessions are not enabled in {await get_intuned_settings_file_name()}. Enable them to use this feature."
        )
    if auth_session_settings.type != "MANUAL":
        raise CLIError(f"AuthSession type is not recorder-based in {await get_intuned_settings_file_name()}")
    start_url = auth_session_settings.start_url
    finish_url = auth_session_settings.finish_url
    if not start_url or not finish_url:
        raise CLIError(
            f"AuthSession type is recorder-based but start_url or finish_url is not set in {await get_intuned_settings_file_name()}"
        )

    return start_url, finish_url
