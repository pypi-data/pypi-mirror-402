"""
Command to show status of persistent browser instances.
"""

import json

from _intuned_runtime_internal.browser.state import delete_browser_state
from _intuned_runtime_internal.browser.state import is_browser_alive
from _intuned_runtime_internal.browser.state import list_browser_states
from _intuned_runtime_internal.browser.state import load_browser_state
from _intuned_runtime_internal.browser.tabs import get_cdp_tabs
from intuned_cli.utils.console import console
from intuned_cli.utils.wrapper import cli_command


@cli_command
async def browser__status(
    *,
    name: str | None = None,
    json_output: bool = False,
):
    """Show status of persistent browser instances.

    If --name is provided, shows status for that specific browser.
    Otherwise, shows status for all browsers.

    Args:
        name (str | None, optional): [--name]. Name of a specific browser to check. Defaults to None (show all).
        json_output (bool, optional): [--json]. Output as JSON instead of formatted console. Defaults to False.
    """
    if name is not None:
        # Show status for specific browser
        state = await load_browser_state(name)
        if state is None:
            if json_output:
                print(json.dumps({"error": f"No browser '{name}' found"}, indent=2))
            else:
                console.print(f"[yellow]No browser '{name}' found.[/yellow]")
            return

        is_alive = await is_browser_alive(state.cdp_address)

        # Get live tab count from CDP
        tab_count = 0
        if is_alive:
            try:
                cdp_tabs = await get_cdp_tabs(state.cdp_address)
                tab_count = len(cdp_tabs)
            except Exception:
                # If we can't get tabs, just show 0
                tab_count = 0

        if json_output:
            output = state.model_dump()
            output["is_running"] = is_alive
            output["tab_count"] = tab_count
            print(json.dumps(output, indent=2))
        else:
            if is_alive:
                console.print(f"[bold green]● Browser '{name}' is running[/bold green]")
                console.print(f"  [bold]CDP Address:[/bold] [cyan]{state.cdp_address}[/cyan]")
                console.print(f"  [bold]CDP Port:[/bold] [cyan]{state.cdp_port}[/cyan]")
                console.print(f"  [bold]PID:[/bold] [cyan]{state.pid}[/cyan]")
                console.print(f"  [bold]Headless:[/bold] [cyan]{state.headless}[/cyan]")
                console.print(f"  [bold]Started at:[/bold] [cyan]{state.started_at}[/cyan]")
                console.print(f"  [bold]Tabs:[/bold] [cyan]{tab_count}[/cyan]")
            else:
                console.print(f"[bold red]○ Browser '{name}' is not running[/bold red] [dim](stale state)[/dim]")
                # Clean up stale state
                await delete_browser_state(name)
                console.print(f"  [dim]Cleaned up stale state file for '{name}'[/dim]")

        if not is_alive and not json_output:
            # Clean up stale state
            await delete_browser_state(name)
        return

    # Show status for all browsers
    states = await list_browser_states()

    if not states:
        if json_output:
            print(json.dumps({"browsers": []}, indent=2))
        else:
            console.print("[yellow]No persistent browsers found.[/yellow]")
            console.print("[dim]Use 'intuned browser start' to start a browser.[/dim]")
        return

    if json_output:
        browsers = []
        for state in states:
            is_alive = await is_browser_alive(state.cdp_address)

            # Get live tab count
            tab_count = 0
            if is_alive:
                try:
                    cdp_tabs = await get_cdp_tabs(state.cdp_address)
                    tab_count = len(cdp_tabs)
                except Exception:
                    tab_count = 0

            browser_data = state.model_dump()
            browser_data["is_running"] = is_alive
            browser_data["tab_count"] = tab_count
            browsers.append(browser_data)

            # Clean up stale state
            if not is_alive:
                await delete_browser_state(state.name)

        print(json.dumps({"browsers": browsers}, indent=2))
    else:
        console.print("[bold]Persistent Browser Instances:[/bold]\n")

        running_count = 0
        for state in states:
            is_alive = await is_browser_alive(state.cdp_address)

            # Get live tab count
            tab_count = 0
            if is_alive:
                try:
                    cdp_tabs = await get_cdp_tabs(state.cdp_address)
                    tab_count = len(cdp_tabs)
                except Exception:
                    tab_count = 0

            if is_alive:
                running_count += 1
                console.print(f"[bold green]● {state.name}[/bold green]")
                console.print(f"  [bold]CDP Address:[/bold] [cyan]{state.cdp_address}[/cyan]")
                console.print(f"  [bold]CDP Port:[/bold] [cyan]{state.cdp_port}[/cyan]")
                console.print(f"  [bold]PID:[/bold] [cyan]{state.pid}[/cyan]")
                console.print(f"  [bold]Headless:[/bold] [cyan]{state.headless}[/cyan]")
                console.print(f"  [bold]Started at:[/bold] [cyan]{state.started_at}[/cyan]")
                console.print(f"  [bold]Tabs:[/bold] [cyan]{tab_count}[/cyan]")
            else:
                console.print(f"[bold red]○ {state.name}[/bold red] [dim](not running - stale state)[/dim]")
                # Clean up stale state
                await delete_browser_state(state.name)
                console.print("  [dim]Cleaned up stale state file[/dim]")
            console.print("")

        console.print(f"[bold]Total:[/bold] {running_count} running, {len(states) - running_count} stale")
