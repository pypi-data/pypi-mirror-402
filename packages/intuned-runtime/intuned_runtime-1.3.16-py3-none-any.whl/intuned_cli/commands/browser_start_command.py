"""
Command to start a persistent browser instance.
"""

from _intuned_runtime_internal.browser.launch_chromium import launch_detached_chromium
from _intuned_runtime_internal.browser.state import create_browser_state
from _intuned_runtime_internal.browser.state import delete_browser_state
from _intuned_runtime_internal.browser.state import find_free_port
from _intuned_runtime_internal.browser.state import is_browser_alive
from _intuned_runtime_internal.browser.state import is_port_in_use
from _intuned_runtime_internal.browser.state import load_browser_state
from _intuned_runtime_internal.browser.state import save_browser_state
from _intuned_runtime_internal.env import get_browser_type
from intuned_cli.utils.console import console
from intuned_cli.utils.error import CLIError
from intuned_cli.utils.wrapper import cli_command

DEFAULT_CDP_PORT = 9222
DEFAULT_BROWSER_NAME = "default"


@cli_command
async def browser__start(
    *,
    name: str = DEFAULT_BROWSER_NAME,
    cdp_port: int = DEFAULT_CDP_PORT,
    headless: bool = False,
):
    """Start a persistent browser instance that can be reused across CLI commands.

    Args:
        name (str, optional): [--name]. Name of the browser instance. Defaults to "default".
        cdp_port (int, optional): [--cdp-port]. CDP port for the browser. Defaults to 9222.
        headless (bool, optional): [--headless]. Run in headless mode. Defaults to False.
    """
    # Check if CamoFox is selected
    browser_type = get_browser_type()
    if browser_type == "camoufox":
        raise CLIError("CamoFox not supported for browser")

    # Check if browser with this name is already running
    existing_state = await load_browser_state(name)
    if existing_state is not None:
        if await is_browser_alive(existing_state.cdp_address):
            raise CLIError(f"Browser '{name}' is already running on port {existing_state.cdp_port}")
        else:
            # Stale state file, clean it up
            await delete_browser_state(name)

    # Check if port is already in use
    if await is_port_in_use(cdp_port):
        if cdp_port != DEFAULT_CDP_PORT:
            # User explicitly specified a port, fail if in use
            raise CLIError(f"Port {cdp_port} already in use")
        # Default port in use, find a free one
        cdp_port = find_free_port()
        console.print(f"[dim]Default port {DEFAULT_CDP_PORT} in use, using port {cdp_port} instead[/dim]")

    console.print(f"[bold]Starting browser '[cyan]{name}[/cyan]' on port [cyan]{cdp_port}[/cyan]...[/bold]")

    # Launch the browser as a detached process
    pid, user_data_dir = await launch_detached_chromium(
        port=cdp_port,
        headless=headless,
    )

    # Create and save browser state
    state = create_browser_state(
        name=name,
        cdp_port=cdp_port,
        pid=pid,
        headless=headless,
    )
    await save_browser_state(state)

    console.print(f"[bold green]Browser '[cyan]{name}[/cyan]' started successfully![/bold green]")
    console.print(f"[bold]CDP Address:[/bold] [cyan]{state.cdp_address}[/cyan]")
    console.print(f"[bold]PID:[/bold] [cyan]{pid}[/cyan]")
    console.print(f"[bold]Headless:[/bold] [cyan]{headless}[/cyan]")
    console.print("")
    console.print("[dim]Use [bold]intuned browser stop[/bold] to stop this browser.[/dim]")
    console.print(f"[dim]Use [bold]--browser-name {name}[/bold] with run/attempt commands to use this browser.[/dim]")
