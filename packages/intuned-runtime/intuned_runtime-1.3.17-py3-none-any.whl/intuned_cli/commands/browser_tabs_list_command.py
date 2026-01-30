"""
Command to list all tabs for a browser instance.
"""

import json

from _intuned_runtime_internal.browser.state import list_browser_states
from _intuned_runtime_internal.browser.state import load_browser_state
from _intuned_runtime_internal.browser.tabs import get_cdp_tabs
from intuned_cli.utils.console import console
from intuned_cli.utils.error import CLIError
from intuned_cli.utils.wrapper import cli_command

DEFAULT_BROWSER_NAME = "default"


@cli_command
async def browser__tabs__list(
    *,
    name: str = DEFAULT_BROWSER_NAME,
    json_output: bool = False,
):
    """List all tabs for a browser instance.

    Args:
        name (str, optional): [--name]. Browser instance name. Defaults to "default".
        json_output (bool, optional): [--json]. Output as JSON instead of formatted console. Defaults to False.
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

    # Convert CDP tabs to our format with 4-char tab_id
    tabs = []
    for cdp_tab in cdp_tabs:
        tab_id = cdp_tab["id"][:4]  # First 4 chars
        tabs.append(
            {
                "tab_id": tab_id,
                "cdp_target_id": cdp_tab["id"],
                "title": cdp_tab.get("title", ""),
                "url": cdp_tab.get("url", ""),
            }
        )

    if json_output:
        output = {
            "browser_name": name,
            "tabs": tabs,
        }
        print(json.dumps(output, indent=2))
    else:
        console.print(f"[bold]Tabs for browser '[cyan]{name}[/cyan]':[/bold]\n")

        if not tabs:
            console.print("[yellow]No tabs found.[/yellow]")
            return

        for tab in tabs:
            console.print(f"[cyan]{tab['tab_id']}[/cyan]: {tab['title']}")
            console.print(f"  URL: [dim]{tab['url']}[/dim]")
            console.print(f"  Target ID: [dim]{tab['cdp_target_id']}[/dim]\n")

        console.print(f"[bold]Total:[/bold] {len(tabs)} tab(s)")
