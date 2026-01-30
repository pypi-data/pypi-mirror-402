import sys

from _intuned_runtime_internal.browser.launch_browser import get_browser_executable_path
from _intuned_runtime_internal.browser.launch_chromium import get_chromium_headless_user_agent
from _intuned_runtime_internal.env import get_browser_type
from intuned_internal_cli.utils.wrapper import internal_cli_command


@internal_cli_command
async def get_headless_user_agent():
    from playwright.async_api import async_playwright

    browser_type = get_browser_type()

    if browser_type == "camoufox":
        print("Camoufox is not supported", sys.stderr)
        sys.exit(1)

    async with async_playwright() as playwright:
        print(
            await get_chromium_headless_user_agent(
                playwright=playwright,
                executable_path=await get_browser_executable_path(browser_type) if browser_type else None,
            )
        )
