"""
Command to stop a persistent browser instance.
"""

import os
import signal

from _intuned_runtime_internal.browser.state import delete_browser_state
from _intuned_runtime_internal.browser.state import load_browser_state
from intuned_cli.utils.console import console
from intuned_cli.utils.error import CLIError
from intuned_cli.utils.wrapper import cli_command

DEFAULT_BROWSER_NAME = "default"


@cli_command
async def browser__stop(
    *,
    name: str = DEFAULT_BROWSER_NAME,
):
    """Stop a persistent browser instance.

    Args:
        name (str, optional): [--name]. Name of the browser instance to stop. Defaults to "default".
    """
    # Load browser state
    state = await load_browser_state(name)
    if state is None:
        raise CLIError(f"No browser '{name}' found. Use 'intuned browser start' to start a browser first.")

    console.print(f"[bold]Stopping browser '[cyan]{name}[/cyan]'...[/bold]")

    # Kill the browser process directly using the stored PID
    try:
        os.kill(state.pid, signal.SIGTERM)
        console.print("[green]Browser process terminated.[/green]")
    except ProcessLookupError:
        console.print("[yellow]Browser process not found (may have already exited).[/yellow]")
    except Exception as kill_error:
        console.print(f"[yellow]Could not kill browser process: {kill_error}[/yellow]")

    # Delete the state file
    await delete_browser_state(name)

    console.print(f"[bold green]Browser '[cyan]{name}[/cyan]' stopped successfully![/bold green]")
