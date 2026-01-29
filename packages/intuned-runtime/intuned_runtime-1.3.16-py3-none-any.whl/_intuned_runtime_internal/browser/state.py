"""
Browser state management for persistent browser instances.

Stores and retrieves browser state in .intuned/browsers/<name>.json files.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from httpx import AsyncClient
from pydantic import BaseModel

BROWSERS_STATE_DIR = ".intuned/browsers"


class BrowserState(BaseModel):
    """State of a persistent browser instance."""

    name: str
    cdp_address: str
    cdp_port: int
    pid: int
    headless: bool
    started_at: str  # ISO format datetime


def get_browsers_state_dir() -> Path:
    """Get the directory where browser state files are stored."""
    return Path(os.getcwd()) / BROWSERS_STATE_DIR


def get_browser_state_path(name: str) -> Path:
    """Get the path to the state file for a specific browser."""
    return get_browsers_state_dir() / f"{name}.json"


async def save_browser_state(state: BrowserState) -> None:
    """Save browser state to a JSON file."""
    state_dir = get_browsers_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)

    state_path = get_browser_state_path(state.name)
    state_path.write_text(state.model_dump_json(indent=2))


async def load_browser_state(name: str) -> Optional[BrowserState]:
    """Load browser state from a JSON file. Returns None if not found."""
    state_path = get_browser_state_path(name)
    if not state_path.exists():
        return None

    try:
        return BrowserState.model_validate_json(state_path.read_text())
    except Exception:
        return None


async def delete_browser_state(name: str) -> bool:
    """Delete browser state file. Returns True if file was deleted."""
    state_path = get_browser_state_path(name)
    if state_path.exists():
        state_path.unlink()
        return True
    return False


async def list_browser_states() -> list[BrowserState]:
    """List all browser states from the browsers directory."""
    state_dir = get_browsers_state_dir()
    if not state_dir.exists():
        return []

    states: list[BrowserState] = []
    for state_file in state_dir.glob("*.json"):
        try:
            state = BrowserState.model_validate_json(state_file.read_text())
            states.append(state)
        except Exception:
            # Skip invalid state files
            continue

    return states


async def is_browser_alive(cdp_address: str) -> bool:
    """Check if a browser is reachable via CDP."""
    try:
        async with AsyncClient(timeout=2) as client:
            response = await client.get(f"{cdp_address}/json/version")
            return response.status_code == 200
    except Exception:
        return False


async def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return False
        except OSError:
            return True


def find_free_port() -> int:
    """Find and return a free port on localhost."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


def create_browser_state(
    name: str,
    cdp_port: int,
    pid: int,
    headless: bool,
) -> BrowserState:
    """Create a new BrowserState instance."""
    return BrowserState(
        name=name,
        cdp_address=f"http://localhost:{cdp_port}",
        cdp_port=cdp_port,
        pid=pid,
        headless=headless,
        started_at=datetime.now().isoformat(),
    )
