import asyncio
import json
import logging
import threading
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Literal
from typing import Optional

from playwright.async_api import Page
from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationError
from waitress.server import BaseWSGIServer
from waitress.server import create_server
from waitress.server import MultiSocketServer

from _intuned_runtime_internal.types import CaptchaSolverSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CaptchaType = Literal[
    "aws",
    "cloudflare",
    "customcaptcha",
    "funcaptcha",
    "geetest",
    "hcaptcha",
    "lemincaptcha",
    "recaptcha",
    "textcaptcha",
]

CaptchaStatus = Literal["attached", "solving", "solved", "error", "detached"]

CaptchaErrorCode = Literal["HIT_LIMIT", "MAX_RETRIES", "UNEXPECTED_SERVER_RESPONSE", "UNEXPECTED_ERROR"]


class CaptchaSolveError(Exception):
    """Exception raised when captcha solving fails."""

    def __init__(self, message: str, captcha_error: "CaptchaError"):
        self.captcha_error = captcha_error
        super().__init__(message)


class CaptchaError(BaseModel):
    code: CaptchaErrorCode
    error: Optional[Any] = None


class Captcha(BaseModel):
    model_config = {
        "populate_by_name": True,
        "serialize_by_alias": True,
    }
    id: str
    tab_id: int = Field(alias="tabId", default=0)
    type: CaptchaType
    status: CaptchaStatus
    error: CaptchaError | None = None
    attempts: int = 0

    def __hash__(self):
        """Make Captcha hashable so it can be used in sets."""
        return hash((self.id, self.tab_id))

    def __eq__(self, other):
        """Two captchas are equal if they have the same id and tab_id."""
        if not isinstance(other, Captcha):
            return False
        return self.id == other.id and self.tab_id == other.tab_id


class CaptchaSubscriber:
    """Subscriber with optional status filter."""

    def __init__(
        self,
        handler: Callable[[Captcha], Awaitable[None] | None],
        status: CaptchaStatus | None = None,
    ):
        self.handler = handler
        self.status = status


class TabCaptchaState:
    tab_id: int
    _captchas: dict[str, Captcha]
    _subscribers: list[CaptchaSubscriber]

    def __init__(self, tab_id: int):
        self.tab_id = tab_id
        self._captchas = {}
        self._subscribers = []

    def subscribe(self, handler: Callable[[Captcha], Awaitable[None] | None], status: CaptchaStatus | None = None):
        self._subscribers.append(CaptchaSubscriber(handler, status))

    def unsubscribe(self, handler: Callable[[Captcha], Awaitable[None] | None], status: CaptchaStatus | None = None):
        # Find and remove subscriber matching both handler and status
        for i, subscriber in enumerate(self._subscribers):
            if subscriber.handler == handler and (subscriber.status == status or status is None):
                self._subscribers.pop(i)
                return

    async def _notify_subscribers(self, captcha: Captcha):
        for subscriber in self._subscribers:
            # Only call handler if no status filter specified or status matches
            if subscriber.status is None or subscriber.status == captcha.status:
                result = subscriber.handler(captcha)
                if asyncio.iscoroutine(result):
                    await result

    async def upsert_captcha(self, captcha: Captcha):
        self._captchas[captcha.id] = captcha
        await self._notify_subscribers(captcha)


class ExtensionServer:
    _tabs: dict[int, TabCaptchaState]
    _server: Optional[MultiSocketServer | BaseWSGIServer] = None
    _thread: Optional[threading.Thread] = None
    _main_loop: Optional[asyncio.AbstractEventLoop] = None

    def __init__(self):
        self._tabs = dict()

    def __call__(self, environ, start_response):
        """WSGI application"""
        path = environ.get("PATH_INFO", "")
        method = environ["REQUEST_METHOD"]

        if path == "/state" and method == "POST":
            return self._handle_ingest(environ, start_response)

        start_response("404 Not Found", [("Content-Type", "application/json")])
        return [json.dumps({"error": "Not found"}).encode()]

    async def _handle_upsert_captcha(self, captcha: Captcha):
        if captcha.tab_id not in self._tabs:
            self._tabs[captcha.tab_id] = TabCaptchaState(captcha.tab_id)
        await self._tabs[captcha.tab_id].upsert_captcha(captcha=captcha)

    def _handle_ingest(self, environ, start_response):
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            body = environ["wsgi.input"].read(content_length)
            data = json.loads(body)
            captcha_data = Captcha(**data)
            if self._main_loop and self._main_loop.is_running():
                asyncio.run_coroutine_threadsafe(self._handle_upsert_captcha(captcha=captcha_data), self._main_loop)
            start_response("200 OK", [("Content-Type", "application/json")])
            return [json.dumps({}).encode()]

        except ValidationError as e:
            start_response("400 Bad Request", [("Content-Type", "application/json")])
            return [json.dumps({"error": e.errors()}).encode()]
        except Exception as e:
            logger.error(f"Error: {e}")
            start_response("500 Internal Server Error", [("Content-Type", "application/json")])
            return [json.dumps({"error": "Internal server error"}).encode()]

    async def start(self, port: int = 3000, host: str = "0.0.0.0") -> None:
        """Start server using daemon thread"""
        if self._server:
            return
        self._main_loop = asyncio.get_running_loop()
        self._server = create_server(self.__call__, host=host, port=port)

        def _run_server():
            try:
                if self._server:
                    self._server.run()
            except OSError as err:
                if err.errno != 9:
                    raise

        self._thread = threading.Thread(target=_run_server, daemon=True)
        self._thread.start()

    async def stop(self):
        if self._server:
            self._server.close()

            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)

    async def get_captchas(self, page: Page, status: CaptchaStatus | None) -> list[Captcha]:
        tab_id = await get_tab_id(page)
        if tab_id not in self._tabs:
            return []
        tab_state = self._tabs[tab_id]
        captchas = list(tab_state._captchas.values())
        if status is None:
            return captchas
        return [captcha for captcha in captchas if captcha.status == status and captcha.tab_id == tab_id]

    async def subscribe(
        self, page: Page, handler: Callable[[Captcha], Awaitable[None] | None], status: CaptchaStatus | None = None
    ):
        tab_id = await get_tab_id(page)
        if tab_id not in self._tabs:
            self._tabs[tab_id] = TabCaptchaState(tab_id)
        tab_state = self._tabs[tab_id]
        tab_state.subscribe(handler, status)

    async def unsubscribe(
        self, page: Page, handler: Callable[[Captcha], Awaitable[None] | None], status: CaptchaStatus | None = None
    ):
        tab_id = await get_tab_id(page)
        if tab_id in self._tabs:
            tab_state = self._tabs[tab_id]
            tab_state.unsubscribe(handler, status)

    def remove_tab(self, tab_id: int):
        """Remove tab state to prevent memory leaks."""
        if tab_id in self._tabs:
            del self._tabs[tab_id]

    async def get_tab_id(self, page: Page) -> int:
        """Get tab ID for a page."""
        return await get_tab_id(page)


extension_server: Optional[ExtensionServer] = None


def get_intuned_extension_server() -> ExtensionServer:
    global extension_server
    if extension_server is None:
        raise RuntimeError("Intuned Extension Server is not initialized.")
    return extension_server


async def setup_intuned_extension_server(captcha_settings: Optional[CaptchaSolverSettings] = None):
    global event_emitter, extension_server
    if captcha_settings is None:
        captcha_settings = CaptchaSolverSettings()
    if not extension_server:
        extension_server = ExtensionServer()

    await extension_server.start(port=captcha_settings.port)


async def clean_intuned_extension_server():
    global event_emitter, extension_server
    if extension_server is not None:
        await extension_server.stop()
        extension_server = None


# Cache tab IDs on the page object to avoid repeated expensive lookups
_TAB_ID_CACHE_ATTR = "__INTUNED_CACHED_TAB_ID__"


async def get_tab_id(page: Page) -> int:
    """Get tab ID for a page with caching to avoid repeated expensive lookups."""
    # Check if we have a cached tab ID
    cached = getattr(page, _TAB_ID_CACHE_ATTR, None)
    if cached is not None and isinstance(cached, int):
        return cached

    tab_id: int | None = None
    try:
        tab_id_result = await page.evaluate("window.__INTUNED_TAB_ID__")
        tab_id = int(tab_id_result)
    except Exception:
        await page.wait_for_function("window.__INTUNED_TAB_ID__ !== undefined", timeout=15_000)
        tab_id_result = await page.evaluate("window.__INTUNED_TAB_ID__")
        tab_id = int(tab_id_result)

    # Cache the result on the page object
    setattr(page, _TAB_ID_CACHE_ATTR, tab_id)
    return tab_id
