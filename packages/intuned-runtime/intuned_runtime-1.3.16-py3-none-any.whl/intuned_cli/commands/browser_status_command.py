"""
Command to show status of persistent browser instances.
"""

from _intuned_runtime_internal.browser.state import delete_browser_state
from _intuned_runtime_internal.browser.state import is_browser_alive
from _intuned_runtime_internal.browser.state import list_browser_states
from _intuned_runtime_internal.browser.state import load_browser_state
from intuned_cli.utils.console import console
from intuned_cli.utils.wrapper import cli_command


@cli_command
async def browser__status(
    *,
    name: str | None = None,
):
    """Show status of persistent browser instances.

    If --name is provided, shows status for that specific browser.
    Otherwise, shows status for all browsers.

    Args:
        name (str | None, optional): [--name]. Name of a specific browser to check. Defaults to None (show all).
    """
    if name is not None:
        # Show status for specific browser
        state = await load_browser_state(name)
        if state is None:
            console.print(f"[yellow]No browser '{name}' found.[/yellow]")
            return

        is_alive = await is_browser_alive(state.cdp_address)
        if is_alive:
            console.print(f"[bold green]● Browser '{name}' is running[/bold green]")
            console.print(f"  [bold]CDP Address:[/bold] [cyan]{state.cdp_address}[/cyan]")
            console.print(f"  [bold]CDP Port:[/bold] [cyan]{state.cdp_port}[/cyan]")
            console.print(f"  [bold]PID:[/bold] [cyan]{state.pid}[/cyan]")
            console.print(f"  [bold]Headless:[/bold] [cyan]{state.headless}[/cyan]")
            console.print(f"  [bold]Started at:[/bold] [cyan]{state.started_at}[/cyan]")
        else:
            console.print(f"[bold red]○ Browser '{name}' is not running[/bold red] [dim](stale state)[/dim]")
            # Clean up stale state
            await delete_browser_state(name)
            console.print(f"  [dim]Cleaned up stale state file for '{name}'[/dim]")
        return

    # Show status for all browsers
    states = await list_browser_states()

    if not states:
        console.print("[yellow]No persistent browsers found.[/yellow]")
        console.print("[dim]Use 'intuned browser start' to start a browser.[/dim]")
        return

    console.print("[bold]Persistent Browser Instances:[/bold]\n")

    running_count = 0
    for state in states:
        is_alive = await is_browser_alive(state.cdp_address)
        if is_alive:
            running_count += 1
            console.print(f"[bold green]● {state.name}[/bold green]")
            console.print(f"  [bold]CDP Address:[/bold] [cyan]{state.cdp_address}[/cyan]")
            console.print(f"  [bold]CDP Port:[/bold] [cyan]{state.cdp_port}[/cyan]")
            console.print(f"  [bold]PID:[/bold] [cyan]{state.pid}[/cyan]")
            console.print(f"  [bold]Headless:[/bold] [cyan]{state.headless}[/cyan]")
            console.print(f"  [bold]Started at:[/bold] [cyan]{state.started_at}[/cyan]")
        else:
            console.print(f"[bold red]○ {state.name}[/bold red] [dim](not running - stale state)[/dim]")
            # Clean up stale state
            await delete_browser_state(state.name)
            console.print("  [dim]Cleaned up stale state file[/dim]")
        console.print("")

    console.print(f"[bold]Total:[/bold] {running_count} running, {len(states) - running_count} stale")
