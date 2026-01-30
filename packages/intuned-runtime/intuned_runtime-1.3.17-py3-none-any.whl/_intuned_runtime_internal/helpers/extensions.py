import asyncio
import functools
import logging
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any
from typing import Optional
from typing import overload
from typing import TypeVar

from playwright.async_api import BrowserContext
from playwright.async_api import Page

from _intuned_runtime_internal.browser.extensions.intuned_extension import is_intuned_extension_enabled
from _intuned_runtime_internal.browser.extensions.intuned_extension import set_auto_solve
from _intuned_runtime_internal.browser.extensions.intuned_extension_server import Captcha
from _intuned_runtime_internal.browser.extensions.intuned_extension_server import CaptchaError
from _intuned_runtime_internal.browser.extensions.intuned_extension_server import CaptchaSolveError
from _intuned_runtime_internal.browser.extensions.intuned_extension_server import CaptchaStatus
from _intuned_runtime_internal.browser.extensions.intuned_extension_server import get_intuned_extension_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T")


# Overload 1: Direct call with page only (callable pattern)
@overload
async def wait_for_captcha_solve(
    page: Page,
    *,
    timeout_s: float = 10.0,
    settle_period: float = 5.0,
) -> None: ...


# Overload 2: Wrapper pattern with page and func
@overload
async def wait_for_captcha_solve(
    *,
    page: Page,
    func: Callable[[], Awaitable[Any]],
    timeout_s: float = 10.0,
    settle_period: float = 5.0,
) -> Any: ...


# Overload 3: Decorator without arguments
@overload
def wait_for_captcha_solve(
    func: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]: ...


# Overload 4: Decorator factory with arguments
@overload
def wait_for_captcha_solve(
    *,
    timeout_s: float = 10.0,
    settle_period: float = 5.0,
    wait_for_network_settled: bool = True,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]: ...


def wait_for_captcha_solve(
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Wait for CAPTCHA solve after performing an action or by itself.

    Usage patterns:
    1. Callable: await wait_for_captcha_solve(page, timeout_s=10.0, settle_period=5.0)
    2. Wrapper: await wait_for_captcha_solve(page=page, func=my_func, timeout_s=10.0, settle_period=5.0)
    3. Decorator: @wait_for_captcha_solve or @wait_for_captcha_solve()
    4. Decorator with options: @wait_for_captcha_solve(timeout_s=10.0, settle_period=5.0, wait_for_network_settled=True)

    Args:
        page: Playwright Page object
        func: Optional callable to execute before waiting for captcha solve
        timeout_s: Maximum time to wait in seconds (default: 10.0)
        settle_period: Time to wait after settled event before checking captcha status in seconds (default: 5.0)
        wait_for_network_settled: Whether to wait for network idle before checking captcha (default: True)
    """

    # Case 1a: Direct call with page only (callable pattern - positional)
    # await wait_for_captcha_solve(page, timeout_s=10.0, settle_period=5.0)
    if len(args) == 1 and isinstance(args[0], Page):
        page = args[0]
        timeout_s = kwargs.get("timeout_s", 10.0)
        settle_period = kwargs.get("settle_period", 5.0)
        return _wait_for_captcha_solve_core(
            page=page,
            func=None,
            timeout_s=timeout_s,
            settle_period=settle_period,
            wait_for_network_settled=False,
        )

    # Case 1b: Direct call with page only (callable pattern - keyword)
    # await wait_for_captcha_solve(page=page, timeout_s=10.0, settle_period=5.0)
    if "page" in kwargs and "func" not in kwargs and len(args) == 0:
        page = kwargs["page"]
        timeout_s = kwargs.get("timeout_s", 10.0)
        settle_period = kwargs.get("settle_period", 5.0)

        if not isinstance(page, Page):
            raise ValueError(
                "No Page object found in function arguments. 'page' parameter must be a Playwright Page object."
            )

        return _wait_for_captcha_solve_core(
            page=page,
            func=None,
            timeout_s=timeout_s,
            settle_period=settle_period,
            wait_for_network_settled=False,
        )

    # Case 2: Wrapper pattern with page and func as keyword arguments
    # await wait_for_captcha_solve(page=page, func=func, timeout_s=10.0, settle_period=5.0)
    if "page" in kwargs and "func" in kwargs:
        page = kwargs["page"]
        func = kwargs["func"]
        timeout_s = kwargs.get("timeout_s", 10.0)
        settle_period = kwargs.get("settle_period", 5.0)
        wait_for_network_settled = kwargs.get("wait_for_network_settled", True)

        if not isinstance(page, Page):
            raise ValueError(
                "No Page object found in function arguments. 'page' parameter must be a Playwright Page object."
            )

        return _wait_for_captcha_solve_core(
            page=page,
            func=func,
            timeout_s=timeout_s,
            settle_period=settle_period,
            wait_for_network_settled=wait_for_network_settled,
        )

    # Case 3: Decorator without arguments
    # @wait_for_captcha_solve
    if len(args) == 1 and callable(args[0]) and not isinstance(args[0], Page):
        func = args[0]
        return _create_decorated_function(func, timeout_s=10.0, settle_period=5.0, wait_for_network_settled=True)  # type: ignore

    # Case 4: Decorator factory with arguments (including empty parentheses)
    # @wait_for_captcha_solve() or @wait_for_captcha_solve(timeout_s=10.0, settle_period=5.0, wait_for_network_settled=True)
    if len(args) == 0 and "page" not in kwargs and "func" not in kwargs:
        timeout_s = kwargs.get("timeout_s", 10.0)
        settle_period = kwargs.get("settle_period", 5.0)
        wait_for_network_settled = kwargs.get("wait_for_network_settled", True)

        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            return _create_decorated_function(
                func,
                timeout_s=timeout_s,
                settle_period=settle_period,
                wait_for_network_settled=wait_for_network_settled,
            )

        return decorator

    raise ValueError(
        "Invalid usage. Valid patterns:\n"
        "1. await wait_for_captcha_solve(page, timeout_s=10.0, settle_period=5.0) or await wait_for_captcha_solve(page=page, timeout_s=10.0, settle_period=5.0)\n"
        "2. await wait_for_captcha_solve(page=page, func=func, timeout_s=10.0, settle_period=5.0)\n"
        "3. @wait_for_captcha_solve or @wait_for_captcha_solve()\n"
        "4. @wait_for_captcha_solve(timeout_s=10.0, settle_period=5.0, wait_for_network_settled=True)"
    )


def _create_decorated_function(
    func: Callable[..., Awaitable[Any]],
    timeout_s: float,
    settle_period: float,
    wait_for_network_settled: bool,
) -> Callable[..., Awaitable[Any]]:
    """Helper to create a decorated function with captcha solve waiting."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Find the page object in function arguments
        page = next((arg for arg in args if isinstance(arg, Page)), None)
        if page is None:
            page = kwargs.get("page")

        if not page or not isinstance(page, Page):
            logger.error(
                "No Page object found in function arguments. The decorated function must have a 'page' parameter or receive a Page object as an argument."
            )
            raise ValueError(
                "No Page object found in function arguments. The decorated function must have a 'page' parameter or receive a Page object as an argument."
            )

        async def func_with_args():
            return await func(*args, **kwargs)

        return await _wait_for_captcha_solve_core(
            page=page,
            func=func_with_args,
            timeout_s=timeout_s,
            settle_period=settle_period,
            wait_for_network_settled=wait_for_network_settled,
        )

    return wrapper


async def _wait_for_captcha_solve_core(
    *,
    page: Page,
    func: Optional[Callable[..., Awaitable[Any]]],
    timeout_s: float = 10.0,
    settle_period: float = 5.0,
    wait_for_network_settled: bool = True,
):
    logger.info(f"Starting captcha solve wait (timeout={timeout_s}s, settle_period={settle_period}s)")
    extension_server = get_intuned_extension_server()

    settled_event = asyncio.Event()
    is_timeout = False
    captchas_appeared = False
    error: CaptchaError | None = None
    result = None
    if func is not None:
        result = await func()

    async def get_pending_captchas():
        return await extension_server.get_captchas(page, "solving")

    async def has_no_pending_captchas():
        return not captchas_appeared or len(await get_pending_captchas()) == 0

    async def maybe_settle():
        if await has_no_pending_captchas():
            logger.info("No pending captchas, settling")
            settled_event.set()

    async def on_captcha_update(captcha: Captcha):
        nonlocal captchas_appeared, error

        solving_captchas = await extension_server.get_captchas(page, "solving")
        error_captchas = await extension_server.get_captchas(page, "error")

        logger.info(f"Captcha update received: solving={len(solving_captchas)}, errors={len(error_captchas)}")

        if len(solving_captchas) > 0:
            captchas_appeared = True
            logger.info(f"Captchas detected: {[c.id for c in solving_captchas]}")

        if len(error_captchas) > 0:
            error = error_captchas[0].error
            logger.info(f"Captcha error detected: {error}")
            await maybe_settle()
        elif len(solving_captchas) == 0:
            await maybe_settle()

    if wait_for_network_settled:
        try:
            await page.wait_for_load_state("networkidle")
        except Exception as e:
            logger.debug(f"Network idle wait failed: {e}")

    initial_pending = await get_pending_captchas()
    if len(initial_pending) > 0:
        captchas_appeared = True
        logger.info(f"Initial pending captchas found: {[c.id for c in initial_pending]}")

    async def timeout_task():
        nonlocal is_timeout
        await asyncio.sleep(timeout_s)
        is_timeout = True
        logger.info("Captcha solve timeout reached")
        settled_event.set()

    await extension_server.subscribe(page, on_captcha_update)
    timeout_handle = asyncio.create_task(timeout_task())

    try:
        await asyncio.sleep(0)
        await maybe_settle()

        while True:
            await settled_event.wait()
            logger.info(f"Settled event received, waiting {settle_period}s before checking")
            await asyncio.sleep(settle_period)

            if error is not None:
                logger.info(f"Raising captcha error: {error.code}")
                raise CaptchaSolveError("CAPTCHA Solve Error", error)

            pending = await get_pending_captchas()
            if await has_no_pending_captchas() or is_timeout:
                if is_timeout and len(pending) > 0:
                    logger.info(f"Timeout with {len(pending)} pending captchas")
                    raise TimeoutError("CAPTCHA Solve timed out with pending captchas.")
                logger.info("Captcha solve completed successfully")
                break
            else:
                logger.info(f"Still have {len(pending)} pending captchas, waiting for more updates")
                settled_event = asyncio.Event()

        return result
    except Exception as e:
        raise e
    finally:
        await extension_server.unsubscribe(page, on_captcha_update)
        try:
            timeout_handle.cancel()
        except:
            pass


async def remove_captcha_event_listener(
    page: Page,
    status: CaptchaStatus,
    f: Callable[[Captcha], Awaitable[None] | None],
):
    """
    Detach a callback from a captcha event.

    Args:
        page: The page to get tab id from
        status: The captcha status to stop listening for
        f: The callback function to remove
    """
    extension_server = get_intuned_extension_server()
    await extension_server.unsubscribe(page, f, status)


async def on_captcha_event(
    page: Page,
    status: CaptchaStatus,
    f: Callable[[Captcha], Awaitable[None] | None],
):
    """
    Register a callback for a captcha event.

    Args:
        page: The page to get tab id from
        status: The captcha status to listen for
        f: The callback function to execute
    """
    extension_server = get_intuned_extension_server()
    await extension_server.subscribe(page, f, status)


async def once_captcha_event(
    page: Page,
    status: CaptchaStatus,
    f: Callable[[Captcha], Awaitable[None] | None],
):
    """
    Register a one-time callback for a captcha event.

    Args:
        page: The page to get tab id from
        status: The captcha status to listen for
        f: The callback function to execute
    """
    extension_server = get_intuned_extension_server()

    async def one_time_handler(captcha: Captcha):
        await extension_server.unsubscribe(page, one_time_handler, status)
        result = f(captcha)
        if asyncio.iscoroutine(result):
            await result

    await extension_server.subscribe(page, one_time_handler, status)


async def pause_captcha_solver(context: BrowserContext) -> None:
    """
    Pause the captcha solver by setting autoSolve flag to false.

    This will disable automatic captcha solving in the browser extension
    while preserving all other settings.

    Args:
        context: Playwright browser context

    Raises:
        RuntimeError: If extension is not enabled or settings cannot be updated
    """
    if not await is_intuned_extension_enabled():
        raise RuntimeError("Intuned extension is not enabled. Cannot pause captcha solver.")

    await set_auto_solve(context, False)


async def resume_captcha_solver(context: BrowserContext) -> None:
    """
    Resume the captcha solver by setting autoSolve flag to true.

    This will re-enable automatic captcha solving in the browser extension.

    Args:
        context: Playwright browser context

    Raises:
        RuntimeError: If extension is not enabled or settings cannot be updated
    """
    if not await is_intuned_extension_enabled():
        raise RuntimeError("Intuned extension is not enabled. Cannot resume captcha solver.")

    await set_auto_solve(context, True)
