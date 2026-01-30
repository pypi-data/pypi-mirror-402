"""
Tab management utilities using CDP HTTP API.

Provides functions to interact with browser tabs via Chrome DevTools Protocol HTTP endpoints.
"""

# refer to https://chromedevtools.github.io/devtools-protocol/ for the endpoints documentation.
# this approach is simpler than using the playwright API because it doesn't require us to create a playwright context.
from httpx import AsyncClient


async def get_cdp_tabs(cdp_address: str) -> list[dict]:
    """
    Fetch current tabs from CDP /json endpoint.

    Args:
        cdp_address: CDP address (e.g., "http://localhost:9222")

    Returns:
        List of tab info dictionaries from CDP

    Example response:
        [
            {
                "id": "1234",
                "type": "page",
                "title": "Google",
                "url": "https://google.com",
                ...
            }
        ]
    """
    async with AsyncClient(timeout=5) as client:
        response = await client.get(f"{cdp_address}/json")
        response.raise_for_status()
        tabs = response.json()
        # Filter to only page type (exclude background pages, extensions, etc.)
        return [tab for tab in tabs if tab.get("type") == "page"]


async def create_cdp_tab(cdp_address: str, url: str = "about:blank") -> dict:
    """
    Create new tab via CDP /json/new endpoint with optional URL.

    Args:
        cdp_address: CDP address (e.g., "http://localhost:9222")
        url: Initial URL for the tab (default: "about:blank")

    Returns:
        Tab info dictionary from CDP

    Example response:
        {
            "id": "1234",
            "type": "page",
            "title": "New Tab",
            "url": "about:blank",
            ...
        }
    """
    async with AsyncClient(timeout=5) as client:
        # CDP /json/new endpoint accepts URL as query parameter
        endpoint = f"{cdp_address}/json/new"
        if url and url != "about:blank":
            endpoint = f"{endpoint}?{url}"
        response = await client.put(endpoint)
        response.raise_for_status()
        return response.json()


async def close_cdp_tab(cdp_address: str, cdp_target_id: str) -> bool:
    """
    Close tab via CDP /json/close/{id} endpoint.

    Args:
        cdp_address: CDP address (e.g., "http://localhost:9222")
        cdp_target_id: Full CDP target ID to close

    Returns:
        True if successful, False otherwise
    """
    try:
        async with AsyncClient(timeout=5) as client:
            response = await client.get(f"{cdp_address}/json/close/{cdp_target_id}")
            return response.status_code == 200
    except Exception:
        return False


async def activate_cdp_tab(cdp_address: str, cdp_target_id: str) -> bool:
    """
    Activate/bring to front a tab via CDP /json/activate/{id} endpoint.

    Args:
        cdp_address: CDP address (e.g., "http://localhost:9222")
        cdp_target_id: Full CDP target ID to activate

    Returns:
        True if successful, False otherwise
    """
    try:
        async with AsyncClient(timeout=5) as client:
            response = await client.get(f"{cdp_address}/json/activate/{cdp_target_id}")
            return response.status_code == 200
    except Exception:
        return False
