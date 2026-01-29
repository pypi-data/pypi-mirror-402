import pytimeparse  # type: ignore

from intuned_cli.controller.authsession import execute_attempt_create_auth_session_cli
from intuned_cli.utils.auth_session_helpers import assert_auth_enabled
from intuned_cli.utils.auth_session_helpers import load_parameters
from intuned_cli.utils.browser_state import resolve_browser_name_to_cdp_url
from intuned_cli.utils.wrapper import cli_command


@cli_command
async def attempt__authsession__create(
    parameters: str,
    /,
    *,
    id: str | None = None,
    proxy: str | None = None,
    timeout: str = "10 min",
    headless: bool = False,
    trace: bool = False,
    keep_browser_open: bool = False,
    cdp_url: str | None = None,
    browser_name: str | None = None,
):
    """Create a new AuthSession

    Args:
        parameters (str): Parameters for the AuthSession command
        id (str | None, optional): [--id]. ID of the AuthSession to use for the command. Defaults to ./auth-sessions-instances/[current timestamp].json.
        proxy (str | None, optional): [--proxy]. Proxy URL to use for the AuthSession command. Defaults to None.
        timeout (str, optional): [--timeout]. Timeout for the AuthSession command - seconds or pytimeparse-formatted string. Defaults to "10 min".
        headless (bool, optional): [--headless]. Run the API in headless mode (default: False). This will not open a browser window.
        trace (bool, optional): [--trace]. Capture a trace of each attempt, useful for debugging. Defaults to False.
        keep_browser_open (bool, optional): [--keep-browser-open]. Keep the last browser open after execution for debugging. Defaults to False.
        cdp_url (str | None, optional): [--cdp-url]. [Experimental] Chrome DevTools Protocol URL to connect to an existing browser instance. Disables proxy, headless, keep_browser_open options. Defaults to None.
        browser_name (str | None, optional): [--browser-name]. Name of a persistent browser instance to use (started via 'intuned browser start'). Defaults to None.
    """
    # Resolve browser_name to cdp_url if provided
    if browser_name is not None:
        cdp_url = await resolve_browser_name_to_cdp_url(browser_name)

    await assert_auth_enabled(auth_type="API")

    auth_session_input = await load_parameters(parameters) or {}

    timeout_value = pytimeparse.parse(timeout)  # type: ignore
    if timeout_value is None:
        raise ValueError(
            f"Invalid timeout format: {timeout}. Please use a valid time format like '10 min' or '600 seconds'."
        )

    await execute_attempt_create_auth_session_cli(
        id=id,
        input_data=auth_session_input,
        headless=headless,
        timeout=timeout_value,
        proxy=proxy,
        trace=trace,
        keep_browser_open=keep_browser_open,
        cdp_url=cdp_url,
    )
