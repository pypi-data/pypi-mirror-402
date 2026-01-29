"""
Centralized configuration constants for the crawler framework.

All timeout values, delay constants, and control variables are defined here.
"""

import asyncio
import logging
import random
from typing import Literal

from playwright.async_api import Locator, Page
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class WaitConfig(BaseModel):
    """
    Configuration for a single wait operation.

    All wait times use milliseconds as the canonical unit.
    Randomization applies a multiplier between 1x and 2x to simulate human behavior.
    """

    model_config = ConfigDict(frozen=True)

    min_ms: int
    randomize: bool = True

    @classmethod
    def create(
        cls,
        value: int | None = None,
        *,
        default: int,
        randomize: bool = True,
    ) -> "WaitConfig":
        """
        Create WaitConfig from optional value with fallback to default.

        Args:
            value: Optional configured timeout from field/action definition
            default: Default minimum timeout constant to use if value is None
            randomize: Whether to apply randomization (default True)

        """
        return cls(
            min_ms=value if value is not None else default,
            randomize=randomize,
        )

    def resolve_ms(self) -> int:
        if self.randomize:
            sampled = random.randint(self.min_ms, self.min_ms * 2)
            logger.debug(f"Wait resolved: {sampled}ms (range: {self.min_ms}-{self.min_ms * 2}ms)")
            return sampled
        logger.debug(f"Wait resolved: {self.min_ms}ms (no randomization)")
        return self.min_ms

    def resolve_seconds(self) -> float:
        return self.resolve_ms() / 1000.0


class WaitExecutor:
    """
    Unified executor for all wait operations.

    Provides consistent interface for delays, element visibility waits,
    and element state waits. All methods accept WaitConfig for timing.
    """

    def __init__(self, page: Page) -> None:
        self._page = page

    async def delay(self, config: WaitConfig) -> None:
        await asyncio.sleep(config.resolve_seconds())

    async def page_timeout(self, config: WaitConfig) -> None:
        await self._page.wait_for_timeout(config.resolve_ms())

    async def wait_visible(self, locator: Locator, config: WaitConfig) -> None:
        await locator.wait_for(state="visible", timeout=config.resolve_ms())

    async def wait_attached(self, locator: Locator, config: WaitConfig) -> None:
        await locator.wait_for(state="attached", timeout=config.resolve_ms())

    async def wait_selector(
        self,
        selector: str,
        config: WaitConfig,
        state: Literal["attached", "detached", "visible", "hidden"] = "visible",
    ) -> None:
        await self._page.wait_for_selector(selector=selector, state=state, timeout=config.resolve_ms())


def random_wait_ms(min_ms: int) -> int:
    """Generate a random wait time in milliseconds between min_ms and min_ms * 2."""
    return WaitConfig(min_ms=min_ms, randomize=True).resolve_ms()


DEFAULT_VIEWPORT_WIDTH = 1920
DEFAULT_VIEWPORT_HEIGHT = 1080

# Cookie Consent Timeouts (milliseconds) - minimum values, actual wait is random [min, min*2]
COOKIE_BANNER_SETTLE_DELAY_MIN_MS = 1000
COOKIE_BANNER_VISIBLE_TIMEOUT_MIN_MS = 1500
COOKIE_ACCEPT_BUTTON_TIMEOUT_MIN_MS = 2500
COOKIE_POST_CONSENT_DELAY_MIN_MS = 500

# Action Timeouts (milliseconds) - minimum values, actual wait is random [min, min*2]
ACTION_PRE_DELAY_MIN_MS = 1000
ACTION_POST_DELAY_MIN_MS = 2500
ACTION_ELEMENT_ATTACHED_TIMEOUT_MIN_MS = 15000
ACTION_WAIT_TIMEOUT_MIN_MS = 15000

# Field Handler Timeouts (milliseconds) - minimum values, actual wait is random [min, min*2]
FIELD_VISIBLE_TIMEOUT_MIN_MS = 5000
FIELD_POST_CLICK_DELAY_MIN_MS = 500
FIELD_TYPE_DELAY_MIN_MS = 25
FIELD_WAIT_AFTER_TYPE_MIN_MS = 500
FIELD_OPTION_VISIBLE_TIMEOUT_MIN_MS = 5000
FIELD_WAIT_AFTER_CLICK_MIN_MS = 250

# Combobox Delays (milliseconds) - minimum values, actual wait is random [min, min*2]
COMBOBOX_PRE_TYPE_DELAY_MIN_MS = 150
COMBOBOX_POST_CLEAR_DELAY_MIN_MS = 100
COMBOBOX_POST_ENTER_DELAY_MIN_MS = 150

# Discovery Timeouts (milliseconds) - minimum values
DISCOVERY_PAGE_LOAD_TIMEOUT_MIN_MS = 15000

# CAPTCHA Timeouts (milliseconds) - minimum values for hardcoded operations
CAPTCHA_CONTAINER_VISIBLE_TIMEOUT_MIN_MS = 5000
CAPTCHA_POST_SCROLL_DELAY_MIN_MS = 500
CAPTCHA_MOUSE_MOVE_DELAY_MIN_MS = 100
CAPTCHA_MOUSE_SETTLE_DELAY_MIN_MS = 200
CAPTCHA_POST_SUBMIT_DELAY_MIN_MS = 1000
CAPTCHA_POST_MODAL_DISMISS_DELAY_MIN_MS = 2000
CAPTCHA_RETRY_DELAY_MIN_MS = 2000
CAPTCHA_POLL_INTERVAL_MS = 500

# CSS Selector Special Characters that need escaping
CSS_SELECTOR_ESCAPE_CHARS = ":[]().#>+~="

# Characters that need escaping in CSS attribute values
CSS_ATTRIBUTE_VALUE_ESCAPE_CHARS = "\"'\\[]"
