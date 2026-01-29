"""
Browser utilities for CLI commands.
"""

from _intuned_runtime_internal.browser.state import delete_browser_state
from _intuned_runtime_internal.browser.state import is_browser_alive
from _intuned_runtime_internal.browser.state import load_browser_state
from intuned_cli.utils.error import CLIError


async def resolve_browser_name_to_cdp_url(browser_name: str) -> str:
    """
    Resolve a browser name to its CDP URL.

    Args:
        browser_name: The name of the browser instance to use.

    Returns:
        The CDP URL of the running browser.

    Raises:
        CLIError: If the browser is not found or not running.
    """
    state = await load_browser_state(browser_name)
    if state is None:
        raise CLIError(
            f"No browser '{browser_name}' found. Use 'intuned browser start --name {browser_name}' to start it first."
        )

    if not await is_browser_alive(state.cdp_address):
        # Clean up stale state
        await delete_browser_state(browser_name)
        raise CLIError(
            f"Browser '{browser_name}' is not running (stale state detected). "
            f"Use 'intuned browser start --name {browser_name}' to start it."
        )

    return state.cdp_address
