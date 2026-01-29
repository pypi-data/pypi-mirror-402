"""
Browser utility functions for the crawler framework.

Shared browser-related utilities like cookie consent handling.
"""

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .config import (
    CAPTCHA_CONTAINER_VISIBLE_TIMEOUT_MIN_MS,
    CAPTCHA_MOUSE_MOVE_DELAY_MIN_MS,
    CAPTCHA_MOUSE_SETTLE_DELAY_MIN_MS,
    CAPTCHA_POLL_INTERVAL_MS,
    CAPTCHA_POST_MODAL_DISMISS_DELAY_MIN_MS,
    CAPTCHA_POST_SCROLL_DELAY_MIN_MS,
    CAPTCHA_POST_SUBMIT_DELAY_MIN_MS,
    CAPTCHA_RETRY_DELAY_MIN_MS,
    COOKIE_ACCEPT_BUTTON_TIMEOUT_MIN_MS,
    COOKIE_BANNER_SETTLE_DELAY_MIN_MS,
    COOKIE_BANNER_VISIBLE_TIMEOUT_MIN_MS,
    COOKIE_POST_CONSENT_DELAY_MIN_MS,
    WaitConfig,
    WaitExecutor,
)
from .exceptions import CrawlerTimeoutError
from .models import CaptchaConfig, CookieConsentConfig
from .utils import setup_logger

logger = setup_logger(__name__)


async def handle_cookie_consent(page: Page, config: CookieConsentConfig, strict: bool) -> None:
    """
    Handle cookie consent banner using configured selectors or shadow DOM.

    Args:
        page: Playwright page instance
        config: Cookie consent configuration
        strict: If True, raise error when banner not found; if False, continue gracefully

    """
    logger.info(f"Checking for cookie consent banner: selector='{config.banner_selector}'")

    waiter = WaitExecutor(page=page)
    banner_settle_delay = WaitConfig.create(config.banner_settle_delay_ms, default=COOKIE_BANNER_SETTLE_DELAY_MIN_MS)
    banner_visible_timeout = WaitConfig.create(
        config.banner_visible_timeout_ms, default=COOKIE_BANNER_VISIBLE_TIMEOUT_MIN_MS
    )
    accept_button_timeout = WaitConfig.create(
        config.accept_button_timeout_ms, default=COOKIE_ACCEPT_BUTTON_TIMEOUT_MIN_MS
    )
    post_consent_delay = WaitConfig.create(config.post_consent_delay_ms, default=COOKIE_POST_CONSENT_DELAY_MIN_MS)

    await waiter.page_timeout(config=banner_settle_delay)

    try:
        banner = page.locator(config.banner_selector)
        banner_count = await banner.count()
        if banner_count == 0:
            if strict:
                raise CrawlerTimeoutError(
                    selector=config.banner_selector,
                    step_name="cookie_consent",
                    timeout_ms=banner_visible_timeout.resolve_ms(),
                )
            logger.info("No cookie consent banner found in DOM")
            return

        try:
            await waiter.wait_visible(locator=banner, config=banner_visible_timeout)
            logger.info("Cookie consent banner visible")
        except PlaywrightTimeoutError:
            logger.info("Cookie consent banner in DOM but not visible, attempting to handle anyway")

        if config.shadow_host_selector and config.accept_button_texts:
            await _handle_shadow_dom_consent(page=page, config=config)
        elif config.accept_selector:
            accept_button = page.locator(config.accept_selector)
            try:
                await waiter.wait_visible(locator=accept_button, config=accept_button_timeout)
                await accept_button.click()
                logger.info(f"Clicked accept button: selector='{config.accept_selector}'")
            except PlaywrightTimeoutError:
                logger.info("Accept button not visible, attempting JavaScript click")
                clicked = await _click_cookie_button_via_js(page=page, config=config)
                if not clicked:
                    raise

        await waiter.page_timeout(config=post_consent_delay)
        logger.info("Cookie consent handling completed")
    except PlaywrightTimeoutError as e:
        if strict:
            raise CrawlerTimeoutError(
                selector=config.banner_selector,
                step_name="cookie_consent",
                timeout_ms=banner_visible_timeout.resolve_ms(),
            ) from e
        logger.info(f"Cookie consent handling skipped: {e}")


async def _click_cookie_button_via_js(page: Page, config: CookieConsentConfig) -> bool:
    """
    Click cookie consent button using JavaScript to bypass blocking layers.

    This handles cases where overlay divs intercept pointer events
    and prevent normal Playwright clicks.

    Args:
        page: Playwright page instance
        config: Cookie consent configuration

    Returns:
        True if button was clicked via JavaScript, False otherwise

    """
    accept_selector = config.accept_selector
    banner_selector = config.banner_selector

    result = await page.evaluate(
        """
        ([acceptSelector, bannerSelector]) => {
            // Try common cookie consent button selectors
            const commonSelectors = [
                acceptSelector,
                '[data-testid*="consent"]',
                '[data-testid*="accept"]',
                'button[class*="consent"]',
                'a[class*="consent"]',
                'button[class*="accept"]',
                'a[class*="accept"]',
            ].filter(s => s);

            for (const selector of commonSelectors) {
                try {
                    const buttons = document.querySelectorAll(selector);
                    for (const button of buttons) {
                        const text = button.textContent?.toLowerCase() || '';
                        if (text.includes('klar') || text.includes('akzept') ||
                            text.includes('accept') || text.includes('agree') ||
                            text.includes('ok') || text.includes('verstanden')) {
                            button.click();
                            return { status: 'clicked', selector: selector, text: text.substring(0, 30) };
                        }
                    }
                } catch (e) {
                    // Continue to next selector
                }
            }

            // Last resort: try to remove the cookie banner entirely
            if (bannerSelector) {
                const banner = document.querySelector(bannerSelector);
                if (banner) {
                    banner.remove();
                    return { status: 'removed_banner' };
                }
            }

            return { status: 'no_button_found' };
        }
        """,
        [accept_selector, banner_selector],
    )

    logger.info(f"JavaScript cookie consent result: {result}")

    return result.get("status") == "clicked"


async def _handle_shadow_dom_consent(page: Page, config: CookieConsentConfig) -> None:
    """
    Handle cookie consent in shadow DOM by evaluating JavaScript.

    Attempts to click an accept button inside the shadow root. Falls back to
    removing the banner element if no matching button is found.

    Args:
        page: Playwright page instance
        config: Cookie consent config with shadow_host_selector and accept_button_texts

    """
    accept_texts = config.accept_button_texts
    shadow_selector = config.shadow_host_selector
    banner_selector = config.banner_selector

    result = await page.evaluate(
        """
        ([shadowSelector, acceptTexts, bannerSelector]) => {
            const host = document.querySelector(shadowSelector);
            if (!host) return { status: 'no_host' };

            const shadowRoot = host.shadowRoot;
            if (!shadowRoot) return { status: 'no_shadow_root' };

            const buttons = shadowRoot.querySelectorAll('button');
            for (const btn of buttons) {
                const text = btn.textContent?.toLowerCase() || '';
                for (const acceptText of acceptTexts) {
                    if (text.includes(acceptText.toLowerCase())) {
                        btn.click();
                        return { status: 'clicked', button: text.substring(0, 30) };
                    }
                }
            }

            // If no button found, remove the banner to prevent blocking
            const banner = document.querySelector(bannerSelector);
            if (banner) {
                banner.remove();
                return { status: 'removed_banner' };
            }

            return { status: 'no_accept_button' };
        }
        """,
        [shadow_selector, accept_texts, banner_selector],
    )

    logger.info(f"Shadow DOM cookie consent result: {result}")


async def handle_captcha(page: Page, config: CaptchaConfig, strict: bool) -> bool:
    """
    Handle CAPTCHA challenge using coordinate-based mouse clicking.

    This function attempts to solve CAPTCHAs like Cloudflare Turnstile by:
    1. Waiting for the CAPTCHA container to appear
    2. Scrolling the container into view
    3. Moving the mouse in a human-like way
    4. Clicking at configured offset coordinates from the container
    5. Waiting for the response input to be filled (indicating solved)

    Note: Cloudflare Turnstile uses advanced bot detection that prevents
    automated solving in most cases. For reliable CAPTCHA solving, consider
    integrating a CAPTCHA solving service.

    Args:
        page: Playwright page instance
        config: CAPTCHA configuration with selectors and click coordinates
        strict: If True, raise error when CAPTCHA not found; if False, continue gracefully

    Returns:
        True if CAPTCHA was solved, False if no CAPTCHA was present

    Raises:
        CrawlerTimeoutError: If CAPTCHA could not be solved within timeout/retries

    """
    logger.info(f"Checking for CAPTCHA: selector='{config.container_selector}'")

    waiter = WaitExecutor(page=page)
    pre_click_delay = WaitConfig(min_ms=config.pre_click_delay_ms, randomize=True)
    container_visible_timeout = WaitConfig.create(
        config.container_visible_timeout_ms, default=CAPTCHA_CONTAINER_VISIBLE_TIMEOUT_MIN_MS
    )
    post_scroll_delay = WaitConfig.create(config.post_scroll_delay_ms, default=CAPTCHA_POST_SCROLL_DELAY_MIN_MS)
    mouse_move_delay = WaitConfig.create(config.mouse_move_delay_ms, default=CAPTCHA_MOUSE_MOVE_DELAY_MIN_MS)
    mouse_settle_delay = WaitConfig.create(config.mouse_settle_delay_ms, default=CAPTCHA_MOUSE_SETTLE_DELAY_MIN_MS)
    post_solve_delay = WaitConfig(min_ms=config.post_solve_delay_ms, randomize=True)
    post_submit_delay = WaitConfig.create(config.post_submit_delay_ms, default=CAPTCHA_POST_SUBMIT_DELAY_MIN_MS)
    dismiss_modal_timeout = WaitConfig(min_ms=config.dismiss_modal_timeout_ms, randomize=False)
    post_modal_dismiss_delay = WaitConfig.create(
        config.post_modal_dismiss_delay_ms, default=CAPTCHA_POST_MODAL_DISMISS_DELAY_MIN_MS
    )
    retry_delay = WaitConfig.create(config.retry_delay_ms, default=CAPTCHA_RETRY_DELAY_MIN_MS)
    poll_interval_ms = config.poll_interval_ms if config.poll_interval_ms is not None else CAPTCHA_POLL_INTERVAL_MS

    await waiter.page_timeout(config=pre_click_delay)

    container = page.locator(config.container_selector)
    container_count = await container.count()

    if container_count == 0:
        if strict:
            raise CrawlerTimeoutError(
                selector=config.container_selector,
                step_name="captcha",
                timeout_ms=container_visible_timeout.resolve_ms(),
            )
        logger.info("No CAPTCHA container found, continuing")
        return False

    try:
        await waiter.wait_visible(locator=container, config=container_visible_timeout)
        logger.info("CAPTCHA container visible")
    except PlaywrightTimeoutError as e:
        if strict:
            raise CrawlerTimeoutError(
                selector=config.container_selector,
                step_name="captcha",
                timeout_ms=container_visible_timeout.resolve_ms(),
            ) from e
        logger.info("CAPTCHA container in DOM but not visible, skipping")
        return False

    response_input = page.locator(config.response_selector)
    existing_response = await response_input.input_value() if await response_input.count() > 0 else ""
    if existing_response:
        logger.info("CAPTCHA already solved (response present)")
        return True

    await container.scroll_into_view_if_needed()
    await waiter.page_timeout(config=post_scroll_delay)

    for attempt in range(1, config.max_retries + 1):
        logger.info(f"CAPTCHA solve attempt {attempt}/{config.max_retries}")

        bounding_box = await container.bounding_box()
        if not bounding_box:
            logger.warning("Could not get CAPTCHA container bounding box")
            continue

        logger.info(
            f"CAPTCHA container bounds: x={bounding_box['x']:.0f}, y={bounding_box['y']:.0f}, "
            f"width={bounding_box['width']:.0f}, height={bounding_box['height']:.0f}"
        )

        click_x = bounding_box["x"] + config.click_offset_x
        click_y = bounding_box["y"] + bounding_box["height"] / 2 + config.click_offset_y

        logger.info(f"Moving mouse to CAPTCHA area: x={click_x:.0f}, y={click_y:.0f}")
        await page.mouse.move(click_x - 50, click_y - 30)
        await waiter.page_timeout(config=mouse_move_delay)
        await page.mouse.move(click_x, click_y)
        await waiter.page_timeout(config=mouse_settle_delay)

        logger.info(f"Clicking CAPTCHA at coordinates: x={click_x:.0f}, y={click_y:.0f}")
        await page.mouse.click(click_x, click_y)

        solved = await _wait_for_captcha_response(
            page=page,
            response_selector=config.response_selector,
            timeout_ms=config.solve_timeout_ms,
            poll_interval_ms=poll_interval_ms,
        )

        if solved:
            logger.info("CAPTCHA solved successfully")
            await waiter.page_timeout(config=post_solve_delay)

            if config.submit_after_solve_selector:
                logger.info(f"Clicking submit button after CAPTCHA: selector='{config.submit_after_solve_selector}'")
                submit_button = page.locator(config.submit_after_solve_selector)
                await submit_button.click()
                await waiter.page_timeout(config=post_submit_delay)

            if config.dismiss_modal_selector:
                logger.info(f"Waiting for modal dismiss button: selector='{config.dismiss_modal_selector}'")
                try:
                    modal_button = page.locator(config.dismiss_modal_selector)
                    await waiter.wait_visible(locator=modal_button, config=dismiss_modal_timeout)
                    await modal_button.click()
                    logger.info(f"Clicked modal dismiss button: selector='{config.dismiss_modal_selector}'")
                    await waiter.page_timeout(config=post_modal_dismiss_delay)
                except PlaywrightTimeoutError:
                    logger.info("Modal dismiss button not found, continuing")

            return True

        logger.warning(f"CAPTCHA not solved on attempt {attempt}")
        await waiter.page_timeout(config=retry_delay)

    raise CrawlerTimeoutError(
        selector=config.container_selector,
        step_name="captcha",
        timeout_ms=config.solve_timeout_ms * config.max_retries,
    )


async def _wait_for_captcha_response(
    page: Page,
    response_selector: str,
    timeout_ms: int,
    poll_interval_ms: int,
) -> bool:
    """
    Wait for CAPTCHA response input to be filled.

    Args:
        page: Playwright page instance
        response_selector: CSS selector for the response input
        timeout_ms: Maximum time to wait
        poll_interval_ms: Interval between polling attempts

    Returns:
        True if response was filled, False if timeout

    """
    elapsed_ms = 0

    while elapsed_ms < timeout_ms:
        response_input = page.locator(response_selector)
        if await response_input.count() > 0:
            value = await response_input.input_value()
            if value:
                return True

        await page.wait_for_timeout(poll_interval_ms)
        elapsed_ms += poll_interval_ms

    return False
