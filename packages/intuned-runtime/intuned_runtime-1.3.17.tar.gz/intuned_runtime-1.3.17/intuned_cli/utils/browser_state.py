"""
Browser utilities for CLI commands.
"""

from _intuned_runtime_internal.browser.state import delete_browser_state
from _intuned_runtime_internal.browser.state import is_browser_alive
from _intuned_runtime_internal.browser.state import load_browser_state
from _intuned_runtime_internal.browser.tabs import get_cdp_tabs
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


async def get_cdp_target_id_from_tab_id(cdp_address: str, tab_id: str) -> str:
    """
    Look up full CDP target ID from a 4-character tab ID using live CDP data.

    Args:
        cdp_address: CDP address of the browser
        tab_id: 4-character tab ID to look up

    Returns:
        Full CDP target ID

    Raises:
        CLIError: If the tab is not found
    """
    try:
        cdp_tabs = await get_cdp_tabs(cdp_address)
    except Exception as e:
        raise CLIError(f"Failed to fetch tabs from browser: {e}") from e

    for tab in cdp_tabs:
        if tab["id"].startswith(tab_id):
            return tab["id"]

    raise CLIError(f"Tab '{tab_id}' not found")


async def get_first_tab_cdp_target_id(cdp_address: str) -> str | None:
    """
    Get the CDP target ID of the first tab.

    Args:
        cdp_address: CDP address of the browser

    Returns:
        Full CDP target ID of the first tab, or None if no tabs
    """
    try:
        cdp_tabs = await get_cdp_tabs(cdp_address)
        if cdp_tabs:
            return cdp_tabs[0]["id"]
        return None
    except Exception:
        return None
