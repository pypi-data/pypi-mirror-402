"""
Command to stop a persistent browser instance.
"""

import json
import os
import signal

from _intuned_runtime_internal.browser.state import delete_browser_state
from _intuned_runtime_internal.browser.state import list_browser_states
from _intuned_runtime_internal.browser.state import load_browser_state
from intuned_cli.utils.console import console
from intuned_cli.utils.error import CLIError
from intuned_cli.utils.wrapper import cli_command

DEFAULT_BROWSER_NAME = "default"


async def stop_single_browser(name: str, json_output: bool = False) -> dict:
    """Stop a single browser instance and return result info."""
    state = await load_browser_state(name)
    if state is None:
        return {
            "browser_name": name,
            "stopped": False,
            "error": f"No browser '{name}' found",
        }

    process_terminated = False
    error_message = None
    try:
        os.kill(state.pid, signal.SIGTERM)
        process_terminated = True
    except ProcessLookupError:
        process_terminated = False
        error_message = "Browser process not found (may have already exited)"
    except Exception as kill_error:
        process_terminated = False
        error_message = f"Could not kill browser process: {kill_error}"

    # Delete the state file
    await delete_browser_state(name)

    result = {
        "browser_name": name,
        "stopped": True,
        "process_terminated": process_terminated,
    }
    if error_message:
        result["warning"] = error_message

    return result


@cli_command
async def browser__stop(
    *,
    name: str = DEFAULT_BROWSER_NAME,
    all_browsers: bool = False,
    json_output: bool = False,
):
    """Stop a persistent browser instance.

    Args:
        name (str, optional): [--name]. Name of the browser instance to stop. Defaults to "default".
        all_browsers (bool, optional): [--all]. Stop all running browser instances. Defaults to False.
        json_output (bool, optional): [--json]. Output as JSON instead of formatted console. Defaults to False.
    """
    if all_browsers:
        # Stop all browsers
        states = await list_browser_states()

        if not states:
            if json_output:
                print(json.dumps({"browsers": [], "message": "No browsers to stop"}, indent=2))
            else:
                console.print("[yellow]No persistent browsers found to stop.[/yellow]")
            return

        if not json_output:
            console.print(f"[bold]Stopping all {len(states)} browser(s)...[/bold]\n")

        results = []
        for state in states:
            result = await stop_single_browser(state.name, json_output)
            results.append(result)

            if not json_output:
                if result.get("process_terminated"):
                    console.print(f"[green]● Stopped '{state.name}'[/green]")
                elif result.get("warning"):
                    console.print(f"[yellow]● Stopped '{state.name}' ({result['warning']})[/yellow]")
                else:
                    console.print(f"[green]● Stopped '{state.name}'[/green]")

        if json_output:
            print(json.dumps({"browsers": results}, indent=2))
        else:
            console.print(f"\n[bold green]All {len(states)} browser(s) stopped successfully![/bold green]")
        return

    # Stop single browser
    state = await load_browser_state(name)
    if state is None:
        raise CLIError(f"No browser '{name}' found. Use 'intuned browser start' to start a browser first.")

    if not json_output:
        console.print(f"[bold]Stopping browser '[cyan]{name}[/cyan]'...[/bold]")

    result = await stop_single_browser(name, json_output)

    if not json_output:
        if result.get("process_terminated"):
            console.print("[green]Browser process terminated.[/green]")
        elif result.get("warning"):
            console.print(f"[yellow]{result['warning']}[/yellow]")

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        console.print(f"[bold green]Browser '[cyan]{name}[/cyan]' stopped successfully![/bold green]")
