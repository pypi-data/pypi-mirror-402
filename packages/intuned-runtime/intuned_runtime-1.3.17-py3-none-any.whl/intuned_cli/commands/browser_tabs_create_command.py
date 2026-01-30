"""
Command to create a new tab in a browser instance.
"""

import json

from _intuned_runtime_internal.browser.state import list_browser_states
from _intuned_runtime_internal.browser.state import load_browser_state
from _intuned_runtime_internal.browser.tabs import create_cdp_tab
from intuned_cli.utils.console import console
from intuned_cli.utils.error import CLIError
from intuned_cli.utils.wrapper import cli_command

DEFAULT_BROWSER_NAME = "default"


@cli_command
async def browser__tabs__create(
    *,
    name: str = DEFAULT_BROWSER_NAME,
    url: str = "about:blank",
    json_output: bool = False,
):
    """Create a new tab in a browser instance.

    Args:
        name (str, optional): [--name]. Browser instance name. Defaults to "default".
        url (str, optional): [--url]. Initial URL for the tab. Defaults to "about:blank".
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

    # Create tab via CDP
    try:
        cdp_tab = await create_cdp_tab(state.cdp_address, url)
    except Exception as e:
        raise CLIError("Failed to create tab") from e

    # Generate tab_id from first 4 chars of CDP target ID
    tab_id = cdp_tab["id"][:4]

    if json_output:
        output = {
            "tab_id": tab_id,
            "cdp_target_id": cdp_tab["id"],
            "title": cdp_tab.get("title", ""),
            "url": cdp_tab.get("url", url),
        }
        print(json.dumps(output, indent=2))
    else:
        console.print(f"[green]Created tab {tab_id}[/green]")
