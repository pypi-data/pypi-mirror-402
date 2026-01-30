"""
Command to close a tab by tab ID.
"""

import json

from _intuned_runtime_internal.browser.state import list_browser_states
from _intuned_runtime_internal.browser.state import load_browser_state
from _intuned_runtime_internal.browser.tabs import close_cdp_tab
from _intuned_runtime_internal.browser.tabs import get_cdp_tabs
from intuned_cli.utils.console import console
from intuned_cli.utils.error import CLIError
from intuned_cli.utils.wrapper import cli_command

DEFAULT_BROWSER_NAME = "default"


@cli_command
async def browser__tabs__close(
    tab_id: str,
    /,
    *,
    name: str = DEFAULT_BROWSER_NAME,
    json_output: bool = False,
):
    """Close a tab by tab ID.

    Args:
        tab_id (str): 4-character tab ID to close.
        name (str, optional): [--name]. Browser instance name. Defaults to "default".
        json_output (bool, optional): [--json]. Output as JSON. Defaults to False.
    """
    state = await load_browser_state(name)
    if state is None:
        # Check if there are any browsers at all
        all_browsers = await list_browser_states()
        if not all_browsers:
            raise CLIError("No browsers currently running. Start one with: intuned browser start")
        else:
            raise CLIError(f"Browser '{name}' not found. Start it with: intuned browser start --name {name}")

    # Fetch live tabs from CDP
    try:
        cdp_tabs = await get_cdp_tabs(state.cdp_address)
    except Exception as e:
        raise CLIError(f"Failed to fetch tabs from browser: {e}") from e

    if len(cdp_tabs) <= 1:
        raise CLIError("Cannot close the last tab")

    # Find the tab by tab_id
    cdp_target_id = None
    for tab in cdp_tabs:
        if tab["id"].startswith(tab_id):
            cdp_target_id = tab["id"]
            break

    if cdp_target_id is None:
        raise CLIError(f"Tab '{tab_id}' not found")

    # Close via CDP
    success = await close_cdp_tab(state.cdp_address, cdp_target_id)
    if not success:
        raise CLIError(f"Failed to close tab {tab_id} via CDP")

    if json_output:
        output = {"closed_tab_id": tab_id, "browser_name": name}
        print(json.dumps(output, indent=2))
    else:
        console.print(f"[green]Closed tab {tab_id}[/green]")
