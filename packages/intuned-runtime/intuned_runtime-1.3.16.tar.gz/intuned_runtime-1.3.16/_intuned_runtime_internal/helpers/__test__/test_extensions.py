import asyncio
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from playwright.async_api import Page

from _intuned_runtime_internal.browser.extensions.intuned_extension_server import Captcha
from _intuned_runtime_internal.browser.extensions.intuned_extension_server import CaptchaError
from _intuned_runtime_internal.browser.extensions.intuned_extension_server import CaptchaErrorCode
from _intuned_runtime_internal.browser.extensions.intuned_extension_server import CaptchaSolveError
from _intuned_runtime_internal.browser.extensions.intuned_extension_server import CaptchaStatus
from _intuned_runtime_internal.helpers.extensions import on_captcha_event
from _intuned_runtime_internal.helpers.extensions import once_captcha_event
from _intuned_runtime_internal.helpers.extensions import remove_captcha_event_listener
from _intuned_runtime_internal.helpers.extensions import wait_for_captcha_solve


class CaptchaStateMock:
    """A mock class to simulate captcha state transitions for testing."""

    initial: Captcha
    transitions: list["CaptchaTransitionMock"]

    def __init__(self, initial: Captcha, transitions: list["CaptchaTransitionMock"]):
        self.initial = initial
        self.transitions = transitions


class CaptchaTransitionMock:
    """Represents a state transition for a captcha at a specific time."""

    time: float
    status: CaptchaStatus
    error_code: CaptchaErrorCode | None

    def __init__(self, time: float, status: CaptchaStatus, error_code: CaptchaErrorCode | None = None):
        self.time = time
        self.status = status
        self.error_code = error_code


@pytest.fixture
def mock_page() -> Mock:
    """Create a mock Page object."""
    page = Mock(spec=Page)
    page.wait_for_load_state = AsyncMock()
    return page


@pytest.fixture
def mock_tab_id():
    """Mock get_tab_id to return a consistent tab ID."""
    with patch(
        "_intuned_runtime_internal.browser.extensions.intuned_extension_server.get_tab_id", AsyncMock(return_value=0)
    ):
        yield 0


@pytest.fixture
def extension_server(mock_tab_id):
    """Create a real ExtensionServer instance for testing."""
    from _intuned_runtime_internal.browser.extensions.intuned_extension_server import ExtensionServer

    server = ExtensionServer()
    # No need to start HTTP server for unit tests
    with patch("_intuned_runtime_internal.helpers.extensions.get_intuned_extension_server", return_value=server):
        yield server
    # Cleanup: clear any state
    server._tabs.clear()


async def run_captcha_test_scenario(
    mock_page: Mock,
    extension_server,
    mock_states: list[CaptchaStateMock],
    timeout: float = 2.0,
    settle_period: float = 0.1,
    expect_error_code: CaptchaErrorCode | None = None,
    expect_timeout: bool = False,
):
    """
    Run a captcha test scenario with multiple captchas and state transitions.

    Args:
        mock_page: Mocked Playwright Page object
        extension_server: Real ExtensionServer instance
        mock_states: List of CaptchaStateMock objects defining captcha states and transitions
        timeout: Timeout value in seconds (default: 2.0)
        settle_period: Settle period value in seconds (default: 0.1)
        expect_error_code: Expected CaptchaErrorCode (expects CaptchaSolveError if provided)
        expect_timeout: Whether to expect a TimeoutError
    """
    # Setup initial captchas using real server
    for state in mock_states:
        await extension_server._handle_upsert_captcha(state.initial)

    async def _simulate_captcha_transitions(state: CaptchaStateMock):
        """Simulate state transitions for a single captcha using real server."""
        spent_time = 0
        for transition in state.transitions:
            await asyncio.sleep(transition.time - spent_time)
            captcha_error = CaptchaError(code=transition.error_code) if transition.error_code else None
            updated_captcha = Captcha(
                id=state.initial.id,
                tabId=state.initial.tab_id,
                type=state.initial.type,
                status=transition.status,
                error=captcha_error,
            )
            spent_time = transition.time
            await extension_server._handle_upsert_captcha(updated_captcha)

    # Handle error expectations
    if expect_error_code:
        task = asyncio.create_task(wait_for_captcha_solve(mock_page, timeout_s=timeout, settle_period=settle_period))
        await asyncio.sleep(0)

        simulate_transition_tasks = [asyncio.create_task(_simulate_captcha_transitions(state)) for state in mock_states]

        with pytest.raises(CaptchaSolveError) as exc_info:
            await task

        assert exc_info.value.captcha_error.code == expect_error_code

        # Cleanup
        for t in simulate_transition_tasks:
            if not t.done():
                t.cancel()
        return

    if expect_timeout:
        task = asyncio.create_task(wait_for_captcha_solve(mock_page, timeout_s=timeout, settle_period=settle_period))
        await asyncio.sleep(0)

        simulate_transition_tasks = [asyncio.create_task(_simulate_captcha_transitions(state)) for state in mock_states]

        with pytest.raises(TimeoutError, match="CAPTCHA Solve timed out with pending captchas."):
            await task

        for t in simulate_transition_tasks:
            if not t.done():
                t.cancel()
        return

    # Handle success case
    task = asyncio.create_task(wait_for_captcha_solve(mock_page, timeout_s=timeout, settle_period=settle_period))
    await asyncio.sleep(0)

    simulate_transition_tasks = [asyncio.create_task(_simulate_captcha_transitions(state)) for state in mock_states]

    try:
        await asyncio.wait_for(task, timeout=None)
    except asyncio.TimeoutError as e:
        task.cancel()
        raise AssertionError("Task should have completed after verification period") from e
    finally:
        # Cleanup
        for t in simulate_transition_tasks:
            if not t.done():
                t.cancel()


class TestUsagePatterns:
    """Test different usage patterns for wait_for_captcha_solve."""

    @pytest.mark.asyncio
    async def test_callable_pattern_positional(self, mock_page, extension_server):
        """Test: await wait_for_captcha_solve(page, timeout_s=10.0)"""
        await wait_for_captcha_solve(mock_page, timeout_s=1.0)

        # Verify network idle is NOT called (callable pattern defaults to wait_for_network_settled=False)
        mock_page.wait_for_load_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_callable_pattern_keyword(self, mock_page, extension_server):
        """Test: await wait_for_captcha_solve(page=page, timeout_s=10.0)"""
        result = await wait_for_captcha_solve(page=mock_page, timeout_s=1.0)

        assert result is None
        mock_page.wait_for_load_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrapper_pattern(self, mock_page, extension_server):
        """Test: await wait_for_captcha_solve(page=page, func=my_func, timeout_s=10.0)"""
        func_called = False
        expected_return = {"result": "success"}

        async def my_func():
            nonlocal func_called
            func_called = True
            return expected_return

        result = await wait_for_captcha_solve(page=mock_page, func=my_func, timeout_s=1.0)

        assert func_called is True
        assert result == expected_return
        mock_page.wait_for_load_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_decorator_without_arguments(self, mock_page, extension_server):
        """Test: @wait_for_captcha_solve"""

        @wait_for_captcha_solve
        async def my_function(page):
            return "decorated_result"

        result = await my_function(mock_page)

        assert result == "decorated_result"

    @pytest.mark.asyncio
    async def test_decorator_factory_with_options(self, mock_page, extension_server):
        """Test: @wait_for_captcha_solve(timeout_s=10.0, wait_for_network_settled=False)"""

        @wait_for_captcha_solve(timeout_s=1.0, wait_for_network_settled=False)
        async def my_function(page):
            return "custom_result"

        result = await my_function(mock_page)

        assert result == "custom_result"
        mock_page.wait_for_load_state.assert_not_called()


class TestCaptchaStateTransitions:
    """Test various captcha state transitions."""

    @pytest.mark.asyncio
    async def test_no_captchas_completes_after_verification(self, mock_page, extension_server):
        """Test that function completes after verification period when no captchas present."""
        result = await wait_for_captcha_solve(mock_page, timeout_s=1.0)
        assert result is None

    @pytest.mark.asyncio
    async def test_captcha_solved_completes_successfully(self, mock_page, extension_server):
        """Test that captcha being solved allows function to complete."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="test1", tabId=0, type="recaptcha", status="solving"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solved"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_captcha_detached_completes_successfully(self, mock_page, extension_server):
        """Test that detached captcha is treated as resolved."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="test1", tabId=0, type="recaptcha", status="solving"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="detached"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_captcha_error_raises_exception(self, mock_page, extension_server):
        """Test that captcha error status raises an exception."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="test1", tabId=0, type="recaptcha", status="solving"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="error", error_code="UNEXPECTED_ERROR"),
                ],
            )
        ]

        await run_captcha_test_scenario(
            mock_page,
            extension_server,
            mock_states,
            expect_error_code="UNEXPECTED_ERROR",
        )

    @pytest.mark.asyncio
    async def test_timeout_with_pending_captchas_raises_error(self, mock_page, extension_server):
        """Test that timeout with pending captchas raises TimeoutError."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="test1", tabId=0, type="recaptcha", status="solving"),
                transitions=[],  # No transitions - captcha stays solving
            )
        ]

        await run_captcha_test_scenario(
            mock_page,
            extension_server,
            mock_states,
            timeout=0.1,
            settle_period=0.05,
            expect_timeout=True,
        )

    @pytest.mark.asyncio
    async def test_attached_to_solving_to_solved(self, mock_page, extension_server):
        """Normal happy path where captcha is detected, solving begins, and completes successfully."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solving"),
                    CaptchaTransitionMock(time=0.15, status="solved"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_attached_to_detached(self, mock_page, extension_server):
        """Captcha detected but immediately removed."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="detached"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_attached_to_solving_to_error(self, mock_page, extension_server):
        """Captcha solve attempt fails after extended solving period."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solving"),
                    CaptchaTransitionMock(time=0.15, status="error", error_code="UNEXPECTED_ERROR"),
                ],
            )
        ]

        await run_captcha_test_scenario(
            mock_page,
            extension_server,
            mock_states,
            expect_error_code="UNEXPECTED_ERROR",
        )

    @pytest.mark.asyncio
    async def test_attached_to_solving_to_detached(self, mock_page, extension_server):
        """Captcha removed mid-solve."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solving"),
                    CaptchaTransitionMock(time=0.1, status="detached"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_visibility_toggle_then_solved(self, mock_page, extension_server):
        """Captcha temporarily becomes hidden, then reappears and solves."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solving"),
                    CaptchaTransitionMock(time=0.1, status="attached"),
                    CaptchaTransitionMock(time=0.12, status="solving"),
                    CaptchaTransitionMock(time=0.25, status="solved"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_visibility_toggle_then_error(self, mock_page, extension_server):
        """Captcha toggles visibility, then fails to solve."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solving"),
                    CaptchaTransitionMock(time=0.1, status="attached"),
                    CaptchaTransitionMock(time=0.12, status="solving"),
                    CaptchaTransitionMock(time=0.25, status="error", error_code="MAX_RETRIES"),
                ],
            )
        ]

        await run_captcha_test_scenario(
            mock_page,
            extension_server,
            mock_states,
            expect_error_code="MAX_RETRIES",
        )

    @pytest.mark.asyncio
    async def test_visibility_toggle_then_detached(self, mock_page, extension_server):
        """Captcha toggles visibility, then gets fully removed."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solving"),
                    CaptchaTransitionMock(time=0.1, status="attached"),
                    CaptchaTransitionMock(time=0.11, status="detached"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_visibility_toggle_solving_then_detached(self, mock_page, extension_server):
        """Captcha toggles visibility, resumes solving, then gets detached."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solving"),
                    CaptchaTransitionMock(time=0.1, status="attached"),
                    CaptchaTransitionMock(time=0.12, status="solving"),
                    CaptchaTransitionMock(time=0.2, status="detached"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_rapid_visibility_toggle_then_solved(self, mock_page, extension_server):
        """Flaky visibility with rapid toggles, eventually solves."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.02, status="solving"),
                    CaptchaTransitionMock(time=0.03, status="attached"),
                    CaptchaTransitionMock(time=0.04, status="solving"),
                    CaptchaTransitionMock(time=0.05, status="attached"),
                    CaptchaTransitionMock(time=0.06, status="solving"),
                    CaptchaTransitionMock(time=0.2, status="solved"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_rapid_visibility_toggle_then_detached(self, mock_page, extension_server):
        """Flaky visibility with rapid toggles, eventually detached."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.02, status="solving"),
                    CaptchaTransitionMock(time=0.03, status="attached"),
                    CaptchaTransitionMock(time=0.04, status="solving"),
                    CaptchaTransitionMock(time=0.05, status="attached"),
                    CaptchaTransitionMock(time=0.06, status="detached"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_instant_toggles_then_solved(self, mock_page, extension_server):
        """Instant state toggles, then solves."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.01, status="solving"),
                    CaptchaTransitionMock(time=0.02, status="attached"),
                    CaptchaTransitionMock(time=0.03, status="solving"),
                    CaptchaTransitionMock(time=0.15, status="solved"),
                ],
            )
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_long_solving_timeout(self, mock_page, extension_server):
        """Captcha takes too long to solve, should timeout before completing."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="attached"),
                transitions=[
                    CaptchaTransitionMock(time=0.01, status="solving"),
                    CaptchaTransitionMock(time=5.0, status="error", error_code="UNEXPECTED_ERROR"),
                ],
            )
        ]

        await run_captcha_test_scenario(
            mock_page,
            extension_server,
            mock_states,
            timeout=1.0,
            settle_period=0.5,
            expect_timeout=True,
        )


class TestNetworkIdleBehavior:
    """Test network idle waiting behavior."""

    @pytest.mark.asyncio
    async def test_waits_for_network_idle_when_enabled(self, mock_page, extension_server):
        """Test that network idle wait is called when enabled."""

        @wait_for_captcha_solve(timeout_s=1.0, wait_for_network_settled=True)
        async def wrapped_func(page):
            return "result"

        await wrapped_func(mock_page)

        mock_page.wait_for_load_state.assert_called_once_with("networkidle")

    @pytest.mark.asyncio
    async def test_skips_network_idle_when_disabled(self, mock_page, extension_server):
        """Test that network idle is skipped when disabled."""

        @wait_for_captcha_solve(timeout_s=1.0, wait_for_network_settled=False)
        async def wrapped_func(page):
            return "result"

        await wrapped_func(mock_page)
        mock_page.wait_for_load_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_network_idle_timeout_is_handled(self, mock_page, extension_server):
        """Test that network idle timeout is caught and execution continues."""
        mock_page.wait_for_load_state.side_effect = Exception("Network timeout")

        @wait_for_captcha_solve(timeout_s=1.0, wait_for_network_settled=True)
        async def dummy_func(page):
            return "result"

        result = await dummy_func(mock_page)

        assert result == "result"


class TestReturnValuePreservation:
    """Test that return values are properly preserved across usage patterns."""

    @pytest.mark.asyncio
    async def test_callable_returns_none(self, mock_page, extension_server):
        """Test that callable pattern returns None."""
        result = await wait_for_captcha_solve(mock_page, timeout_s=1.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_wrapper_preserves_return_value(self, mock_page, extension_server):
        """Test that wrapper pattern preserves function return value."""
        expected_value = {"data": [1, 2, 3], "status": "success"}

        async def my_func():
            return expected_value

        result = await wait_for_captcha_solve(page=mock_page, func=my_func, timeout_s=1.0)

        assert result == expected_value

    @pytest.mark.asyncio
    async def test_decorator_preserves_return_value(self, mock_page, extension_server):
        """Test that decorator preserves return value."""

        @wait_for_captcha_solve
        async def my_function(page):
            return "decorated_value"

        result = await my_function(mock_page)

        assert result == "decorated_value"


class TestMultipleCaptchas:
    """Test scenarios with multiple captchas."""

    @pytest.mark.asyncio
    async def test_multiple_captchas_both_solve(self, mock_page, extension_server):
        """Test with 2 captchas that both solve at different times."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="solving"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solved"),
                ],
            ),
            CaptchaStateMock(
                initial=Captcha(id="captcha2", tabId=0, type="hcaptcha", status="solving"),
                transitions=[
                    CaptchaTransitionMock(time=0.1, status="solved"),
                ],
            ),
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)

    @pytest.mark.asyncio
    async def test_multiple_captchas_one_errors(self, mock_page, extension_server):
        """Test that one erroring captcha fails the entire operation."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="solving"),
                transitions=[],  # Stays solving
            ),
            CaptchaStateMock(
                initial=Captcha(id="captcha2", tabId=0, type="hcaptcha", status="solving"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="error", error_code="HIT_LIMIT"),
                ],
            ),
        ]

        await run_captcha_test_scenario(
            mock_page,
            extension_server,
            mock_states,
            expect_error_code="HIT_LIMIT",
        )

    @pytest.mark.asyncio
    async def test_staggered_captcha_resolution(self, mock_page, extension_server):
        """Test with 3 captchas resolving at different times."""
        mock_states = [
            CaptchaStateMock(
                initial=Captcha(id="captcha1", tabId=0, type="recaptcha", status="solving"),
                transitions=[
                    CaptchaTransitionMock(time=0.05, status="solved"),
                ],
            ),
            CaptchaStateMock(
                initial=Captcha(id="captcha2", tabId=0, type="hcaptcha", status="solving"),
                transitions=[
                    CaptchaTransitionMock(time=0.1, status="detached"),
                ],
            ),
            CaptchaStateMock(
                initial=Captcha(id="captcha3", tabId=0, type="funcaptcha", status="solving"),
                transitions=[
                    CaptchaTransitionMock(time=0.15, status="solved"),
                ],
            ),
        ]

        await run_captcha_test_scenario(mock_page, extension_server, mock_states)


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_decorator_without_page_raises_error(self, extension_server):
        """Test that decorator without page parameter raises ValueError."""

        @wait_for_captcha_solve
        async def my_function():
            return "result"

        with pytest.raises(ValueError, match="No Page object found"):
            await my_function()

    @pytest.mark.asyncio
    async def test_subscribes_and_unsubscribes(self, mock_page, extension_server):
        """Test that subscribe and unsubscribe are called properly."""
        with patch.object(extension_server, "subscribe") as mock_sub, patch.object(
            extension_server, "unsubscribe"
        ) as mock_unsub:
            await wait_for_captcha_solve(mock_page, timeout_s=1.0)
            mock_sub.assert_called_once()
            mock_unsub.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribes_even_on_error(self, mock_page, extension_server):
        """Test that unsubscribe is called even when error occurs."""
        solving_captcha = Captcha(id="test1", tabId=0, type="recaptcha", status="solving")
        await extension_server._handle_upsert_captcha(solving_captcha)

        with patch.object(extension_server, "unsubscribe") as mock_unsub:
            with pytest.raises(TimeoutError):
                await wait_for_captcha_solve(mock_page, timeout_s=0.1, settle_period=0.05)
            mock_unsub.assert_called_once()


class TestOnCaptchaEvent:
    """Test on_captcha_event functionality."""

    @pytest.mark.asyncio
    async def test_on_captcha_event_calls_callback_for_matching_status(self, mock_page, extension_server):
        """Test that callback is called when captcha with matching status is received."""
        received_captchas: list[Captcha] = []

        async def callback(captcha: Captcha):
            received_captchas.append(captcha)

        await on_captcha_event(mock_page, "solved", callback)

        # Trigger a captcha with matching status
        solved_captcha = Captcha(id="test1", tabId=0, type="recaptcha", status="solved")
        await extension_server._handle_upsert_captcha(solved_captcha)

        assert len(received_captchas) == 1
        assert received_captchas[0].id == "test1"
        assert received_captchas[0].status == "solved"

    @pytest.mark.asyncio
    async def test_on_captcha_event_ignores_non_matching_status(self, mock_page, extension_server):
        """Test that callback is NOT called when captcha status doesn't match."""
        received_captchas: list[Captcha] = []

        async def callback(captcha: Captcha):
            received_captchas.append(captcha)

        await on_captcha_event(mock_page, "solved", callback)

        # Trigger a captcha with non-matching status
        solving_captcha = Captcha(id="test1", tabId=0, type="recaptcha", status="solving")
        await extension_server._handle_upsert_captcha(solving_captcha)

        assert len(received_captchas) == 0

    @pytest.mark.asyncio
    async def test_on_captcha_event_calls_callback_multiple_times(self, mock_page, extension_server):
        """Test that callback is called for each matching captcha event."""
        received_captchas: list[Captcha] = []

        async def callback(captcha: Captcha):
            received_captchas.append(captcha)

        await on_captcha_event(mock_page, "solved", callback)

        # Trigger multiple captchas with matching status
        await extension_server._handle_upsert_captcha(Captcha(id="test1", tabId=0, type="recaptcha", status="solved"))
        await extension_server._handle_upsert_captcha(Captcha(id="test2", tabId=0, type="hcaptcha", status="solved"))

        assert len(received_captchas) == 2
        assert received_captchas[0].id == "test1"
        assert received_captchas[1].id == "test2"

    @pytest.mark.asyncio
    async def test_on_captcha_event_sync_callback(self, mock_page, extension_server):
        """Test that synchronous callbacks work correctly."""
        received_captchas: list[Captcha] = []

        def sync_callback(captcha: Captcha):
            received_captchas.append(captcha)

        await on_captcha_event(mock_page, "error", sync_callback)

        error_captcha = Captcha(
            id="test1", tabId=0, type="recaptcha", status="error", error=CaptchaError(code="UNEXPECTED_ERROR")
        )
        await extension_server._handle_upsert_captcha(error_captcha)

        assert len(received_captchas) == 1
        assert received_captchas[0].status == "error"


class TestOnceCaptchaEvent:
    """Test once_captcha_event functionality."""

    @pytest.mark.asyncio
    async def test_once_captcha_event_calls_callback_only_once(self, mock_page, extension_server):
        """Test that callback is called only once for matching status."""
        received_captchas: list[Captcha] = []

        async def callback(captcha: Captcha):
            received_captchas.append(captcha)

        await once_captcha_event(mock_page, "solved", callback)

        # Trigger multiple captchas with matching status
        await extension_server._handle_upsert_captcha(Captcha(id="test1", tabId=0, type="recaptcha", status="solved"))
        await extension_server._handle_upsert_captcha(Captcha(id="test2", tabId=0, type="hcaptcha", status="solved"))

        # Should only receive the first one
        assert len(received_captchas) == 1
        assert received_captchas[0].id == "test1"

    @pytest.mark.asyncio
    async def test_once_captcha_event_receives_all_events_until_match(self, mock_page, extension_server):
        """Test that callback only receives matching events, and unsubscribes after first match."""
        received_captchas: list[Captcha] = []

        async def callback(captcha: Captcha):
            received_captchas.append(captcha)

        await once_captcha_event(mock_page, "solved", callback)

        # Non-matching status - callback is NOT called due to server-side filtering
        await extension_server._handle_upsert_captcha(Captcha(id="test1", tabId=0, type="recaptcha", status="solving"))
        assert len(received_captchas) == 0

        # Matching status - triggers callback and unsubscribes
        await extension_server._handle_upsert_captcha(Captcha(id="test2", tabId=0, type="recaptcha", status="solved"))
        assert len(received_captchas) == 1
        assert received_captchas[0].id == "test2"

        # After match, no more events should be received
        await extension_server._handle_upsert_captcha(Captcha(id="test3", tabId=0, type="recaptcha", status="solved"))
        assert len(received_captchas) == 1  # Still 1, not 2

    @pytest.mark.asyncio
    async def test_once_captcha_event_unsubscribes_after_match(self, mock_page, extension_server):
        """Test that once_captcha_event unsubscribes after first matching event."""
        call_count = 0

        async def callback(captcha: Captcha):
            nonlocal call_count
            call_count += 1

        await once_captcha_event(mock_page, "solved", callback)

        # First matching event
        await extension_server._handle_upsert_captcha(Captcha(id="test1", tabId=0, type="recaptcha", status="solved"))
        assert call_count == 1

        # Second matching event - should NOT trigger because unsubscribed
        await extension_server._handle_upsert_captcha(Captcha(id="test2", tabId=0, type="recaptcha", status="solved"))
        assert call_count == 1  # Still 1, not 2

    @pytest.mark.asyncio
    async def test_once_captcha_event_sync_callback(self, mock_page, extension_server):
        """Test that synchronous callbacks work correctly with once_captcha_event."""
        received_captchas: list[Captcha] = []

        def sync_callback(captcha: Captcha):
            received_captchas.append(captcha)

        await once_captcha_event(mock_page, "detached", sync_callback)

        await extension_server._handle_upsert_captcha(Captcha(id="test1", tabId=0, type="recaptcha", status="detached"))

        assert len(received_captchas) == 1
        assert received_captchas[0].status == "detached"


class TestRemoveCaptchaEventListener:
    """Test remove_captcha_event_listener functionality."""

    @pytest.mark.asyncio
    async def test_remove_captcha_event_listener_stops_callback(self, mock_page, extension_server):
        """Test that removing listener stops further callbacks."""
        received_captchas: list[Captcha] = []

        async def callback(captcha: Captcha):
            received_captchas.append(captcha)

        await on_captcha_event(mock_page, "solved", callback)

        # First event should be received
        await extension_server._handle_upsert_captcha(Captcha(id="test1", tabId=0, type="recaptcha", status="solved"))
        assert len(received_captchas) == 1

        # Remove the listener
        await remove_captcha_event_listener(mock_page, "solved", callback)

        # Second event should NOT be received
        await extension_server._handle_upsert_captcha(Captcha(id="test2", tabId=0, type="recaptcha", status="solved"))
        assert len(received_captchas) == 1  # Still 1, not 2

    @pytest.mark.asyncio
    async def test_remove_captcha_event_listener_handles_missing_listener(self, mock_page, extension_server):
        """Test that removing a non-existent listener doesn't raise an error."""

        async def callback(captcha: Captcha):
            pass

        # Should not raise an error
        await remove_captcha_event_listener(mock_page, "solved", callback)
