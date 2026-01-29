import json
import os

from _intuned_runtime_internal.browser import launch_browser
from _intuned_runtime_internal.browser.storage_state import set_storage_state
from _intuned_runtime_internal.run.intuned_settings import load_intuned_settings
from _intuned_runtime_internal.types.run_types import StorageState
from intuned_internal_cli.utils.wrapper import internal_cli_command


@internal_cli_command
async def project__auth_session__load(
    *,
    cdp_address: str,
    auth_session_path: str,
):
    """
    Load an AuthSession to a browser.

    Args:
        cdp_address (str): The CDP address of the browser to load the AuthSession to.
        auth_session_path (str): Path to the AuthSession file.
    """
    intuned_settings = await load_intuned_settings()
    if not intuned_settings.auth_sessions.enabled:
        raise Exception("AuthSessions are not enabled")

    async with launch_browser(
        cdp_address=cdp_address,
    ) as (context, _):
        auth_session_path = os.path.join(os.getcwd(), auth_session_path)
        if not os.path.exists(auth_session_path):
            raise Exception("AuthSession file does not exist")

        with open(auth_session_path) as f:
            auth_session = StorageState(**json.load(f))

        await set_storage_state(context, auth_session)
