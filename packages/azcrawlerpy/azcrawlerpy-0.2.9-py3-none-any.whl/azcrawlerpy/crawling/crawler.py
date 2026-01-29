"""
Main FormCrawler class for navigating and filling multi-step web forms.

This module contains the core crawler implementation that orchestrates
field handlers and action executors to complete form workflows.

Uses Camoufox anti-detect browser exclusively for all crawling operations.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from browserforge.fingerprints import Screen
from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .actions import get_action_executor
from .browser_utils import handle_captcha, handle_cookie_consent
from .config import DEFAULT_VIEWPORT_HEIGHT, DEFAULT_VIEWPORT_WIDTH
from .data_extraction import _apply_regex, extract_data
from .diagnostics import CrawlContext, capture_page_diagnostics, write_diagnostic_json
from .exceptions import CrawlerError, CrawlerTimeoutError
from .field_handlers import get_field_handler
from .models import (
    CrawlerBrowserConfig,
    CrawlResult,
    DebugMode,
    InMemoryCrawlResult,
    Instructions,
    StepDefinition,
    StepExtractionDefinition,
)
from .utils import setup_logger

_default_logger = setup_logger(__name__)


@dataclass
class _CrawlState:
    """
    Internal state for a single crawl execution.

    Tracks debug configuration, output paths, screenshot numbering,
    in-memory results, and extracted data during the crawl lifecycle.
    """

    debug_mode: DebugMode
    output_dir: Path | None
    context: CrawlContext
    screenshot_counter: int = 0
    current_step_name: str | None = None
    in_memory_screenshots: list[bytes] = field(default_factory=list)
    extracted_data: dict[str, Any] = field(default_factory=dict)


class FormCrawler:
    """
    Crawler for navigating and filling multi-step web forms.

    Uses Camoufox anti-detect browser which provides C++ level fingerprint
    spoofing that is undetectable by JavaScript-based bot detection.

    This class provides the main interface for automating form completion
    based on JSON instructions. It handles:
    - Multi-step wizard forms
    - Various field types (text, dropdown, radio, etc.)
    - Navigation between form steps
    - Waiting for AJAX-loaded content
    - Saving final page HTML and screenshots
    """

    def __init__(
        self,
        headless: bool | Literal["virtual"],
        browser_config: CrawlerBrowserConfig | None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._headless: bool | Literal["virtual"] = headless
        self._browser_config: CrawlerBrowserConfig | None = browser_config
        self._logger: logging.Logger = logger if logger is not None else _default_logger

        self._logger.info(f"FormCrawler initialized: headless={headless}")
        if browser_config:
            self._logger.info(f"Browser config: {browser_config.model_dump_json(indent=2)}")

    async def crawl(
        self,
        url: str,
        input_data: dict[str, Any],
        instructions: dict[str, Any],
        output_dir: Path | None,
        debug_mode: DebugMode | str = DebugMode.ALL,
        strict: bool = True,
    ) -> CrawlResult | InMemoryCrawlResult:
        """
        Navigate and fill the form, returning results.

        Args:
            url: Starting URL where the form begins
            input_data: Field values to fill (key-value pairs)
            instructions: Navigation and field selectors (JSON structure)
            output_dir: Directory to save HTML and screenshots. If None, returns in-memory result.
            debug_mode: Screenshot mode (none, start, end, all)
            strict: If True, raise errors when elements not found; if False, continue gracefully

        Returns:
            CrawlResult with paths to saved files when output_dir is provided,
            InMemoryCrawlResult with in-memory data when output_dir is None.

        """
        if isinstance(debug_mode, str):
            debug_mode = DebugMode(debug_mode)

        validated_instructions = Instructions.model_validate(instructions)

        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)

        debug_enabled = debug_mode != DebugMode.NONE
        state = _CrawlState(
            debug_mode=debug_mode,
            output_dir=output_dir,
            context=CrawlContext(output_dir=output_dir, debug_enabled=debug_enabled),
        )

        self._logger.info(
            f"Starting crawl: url='{url}' steps={len(validated_instructions.steps)} debug='{debug_mode.value}'"
        )

        instruction_browser_config = validated_instructions.browser_config
        viewport_width = (
            instruction_browser_config.viewport_width if instruction_browser_config else DEFAULT_VIEWPORT_WIDTH
        )
        viewport_height = (
            instruction_browser_config.viewport_height if instruction_browser_config else DEFAULT_VIEWPORT_HEIGHT
        )

        self._logger.info("Using Camoufox anti-detect browser")

        screen_constraints = Screen(max_width=viewport_width, max_height=viewport_height)
        proxy_kwargs = self._build_proxy_kwargs()

        async with AsyncCamoufox(
            headless=self._headless,
            screen=screen_constraints,
            **proxy_kwargs,
        ) as browser:
            page_kwargs = self._build_page_kwargs()
            page = await browser.new_page(**page_kwargs)

            self._setup_event_handlers(page=page, state=state)

            if self._browser_config and self._browser_config.init_scripts:
                for script in self._browser_config.init_scripts:
                    await page.add_init_script(script=script)
                self._logger.info(f"Injected {len(self._browser_config.init_scripts)} init scripts")

            try:
                await page.goto(url=url, wait_until="networkidle")
                self._logger.info(f"Navigated to starting URL: url='{url}'")

                if validated_instructions.cookie_consent:
                    await handle_cookie_consent(
                        page=page,
                        config=validated_instructions.cookie_consent,
                        strict=strict,
                    )

                if debug_mode in (DebugMode.START, DebugMode.ALL):
                    await self._take_debug_screenshot(page=page, label="start", state=state)

                steps_completed = 0
                for step in validated_instructions.steps:
                    await self._process_step(
                        page=page,
                        step=step,
                        input_data=input_data,
                        state=state,
                        strict=strict,
                    )
                    steps_completed += 1

                if validated_instructions.captcha:
                    await handle_captcha(
                        page=page,
                        config=validated_instructions.captcha,
                        strict=strict,
                    )

                return await self._capture_final_page(
                    page=page,
                    instructions=validated_instructions,
                    steps_completed=steps_completed,
                    url=url,
                    input_data=input_data,
                    raw_instructions=instructions,
                    state=state,
                    strict=strict,
                )

            except CrawlerError as e:
                if state.context.debug_enabled:
                    await self._capture_error_diagnostics(page=page, error=e, state=state)
                raise

    def _build_proxy_kwargs(self) -> dict[str, Any]:
        """Build proxy kwargs for AsyncCamoufox if proxy is configured."""
        if self._browser_config is None or self._browser_config.proxy is None:
            return {}

        proxy_config = self._browser_config.proxy
        proxy_dict: dict[str, str] = {"server": proxy_config.server}
        if proxy_config.username is not None:
            proxy_dict["username"] = proxy_config.username
        if proxy_config.password is not None:
            proxy_dict["password"] = proxy_config.password

        self._logger.info(f"Using proxy: server='{proxy_config.server}'")
        return {"proxy": proxy_dict}

    def _build_page_kwargs(self) -> dict[str, Any]:
        """Build page kwargs for browser.new_page() if SSL bypass is configured."""
        if self._browser_config is None or self._browser_config.ignore_https_errors is None:
            return {}

        self._logger.info(f"Ignoring HTTPS errors: ignore_https_errors={self._browser_config.ignore_https_errors}")
        return {"ignore_https_errors": self._browser_config.ignore_https_errors}

    def _setup_event_handlers(self, page: Page, state: _CrawlState) -> None:
        def on_console(msg: Any) -> None:
            state.context.console_messages.append(
                {
                    "type": msg.type,
                    "text": msg.text,
                }
            )

        def on_request_failed(request: Any) -> None:
            state.context.failed_requests.append(
                {
                    "url": request.url,
                    "method": request.method,
                    "failure": request.failure,
                }
            )

        page.on("console", on_console)
        page.on("requestfailed", on_request_failed)

    async def _capture_error_diagnostics(
        self,
        page: Page,
        error: CrawlerError,
        state: _CrawlState,
    ) -> None:
        failed_selector = getattr(error, "selector", None)
        step_name = state.current_step_name

        label = step_name if step_name else "unknown"

        diagnostics = await capture_page_diagnostics(
            page=page,
            context=state.context,
            failed_selector=failed_selector,
            step_name=step_name,
            label=label,
        )

        error.with_diagnostics(diagnostics)

        if state.output_dir is not None:
            write_diagnostic_json(
                output_dir=state.output_dir,
                error=error,
                diagnostics=diagnostics,
            )

    async def _take_debug_screenshot(self, page: Page, label: str, state: _CrawlState) -> None:
        state.screenshot_counter += 1

        if state.output_dir is not None:
            filename = f"debug_{state.screenshot_counter:03d}_{label}.png"
            screenshot_path = state.output_dir / filename
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self._logger.info(f"Debug screenshot: path='{screenshot_path}'")
        else:
            screenshot_bytes = await page.screenshot(full_page=True)
            state.in_memory_screenshots.append(screenshot_bytes)
            self._logger.info(f"Debug screenshot captured in-memory: label='{label}'")

    async def _extract_step_data(
        self,
        page: Page,
        extractions: list[StepExtractionDefinition],
        step_name: str,
        state: _CrawlState,
    ) -> None:
        for extraction in extractions:
            if extraction.wait_before_ms is not None:
                await page.wait_for_timeout(timeout=extraction.wait_before_ms)
                self._logger.info(f"Step extraction wait_before: ms={extraction.wait_before_ms} step='{step_name}'")

            if extraction.click_before is not None:
                if extraction.dismiss_modal_selector is not None and not (extraction.force_click or False):
                    await page.click(selector=extraction.click_before, force=True)
                    self._logger.info(
                        f"Step extraction click (force for modal): selector='{extraction.click_before}' step='{step_name}'"
                    )
                    await page.evaluate(f"document.querySelector('{extraction.click_before}').click()")
                    self._logger.info(
                        f"Step extraction JS click: selector='{extraction.click_before}' step='{step_name}'"
                    )
                else:
                    await page.click(selector=extraction.click_before, force=extraction.force_click or False)
                    self._logger.info(
                        f"Step extraction click: selector='{extraction.click_before}' force={extraction.force_click} step='{step_name}'"
                    )

                if extraction.wait_after_click_ms is not None:
                    await page.wait_for_timeout(timeout=extraction.wait_after_click_ms)

            locator = page.locator(extraction.selector)
            count = await locator.count()

            if count == 0:
                self._logger.warning(
                    f"Step extraction no match: name='{extraction.name}' selector='{extraction.selector}' step='{step_name}'"
                )
                state.extracted_data[extraction.name] = None
                continue

            element = locator.first
            raw_value = (
                await element.get_attribute(name=extraction.attribute)
                if extraction.attribute
                else await element.text_content()
            )

            processed_value = _apply_regex(value=raw_value, pattern=extraction.regex)
            state.extracted_data[extraction.name] = processed_value
            self._logger.info(f"Step extraction: name='{extraction.name}' value='{processed_value}' step='{step_name}'")

            if extraction.dismiss_modal_selector is not None:
                modal_locator = page.locator(extraction.dismiss_modal_selector)
                if await modal_locator.count() > 0:
                    await modal_locator.first.click(force=True)
                    self._logger.info(
                        f"Step extraction dismissed modal: selector='{extraction.dismiss_modal_selector}' step='{step_name}'"
                    )

    async def _process_step(
        self,
        page: Page,
        step: StepDefinition,
        input_data: dict[str, Any],
        state: _CrawlState,
        strict: bool,
    ) -> None:
        state.current_step_name = step.name
        self._logger.info(f"Processing step: name='{step.name}'")

        try:
            await page.wait_for_selector(
                selector=step.wait_for,
                state="visible",
                timeout=step.timeout_ms,
            )
            self._logger.info(f"Wait condition met: selector='{step.wait_for}' step='{step.name}'")
        except (PlaywrightTimeoutError, PlaywrightError) as e:
            if strict:
                raise CrawlerTimeoutError(
                    selector=step.wait_for,
                    step_name=step.name,
                    timeout_ms=step.timeout_ms,
                ) from e
            self._logger.warning(f"Step wait timeout (non-strict): selector='{step.wait_for}' step='{step.name}'")

        if step.data_extraction is not None:
            await self._extract_step_data(
                page=page,
                extractions=step.data_extraction,
                step_name=step.name,
                state=state,
            )

        for field_def in step.fields:
            try:
                handler = get_field_handler(field_type=field_def.type, step_name=step.name)
                await handler.handle(
                    page=page,
                    field=field_def,
                    input_data=input_data,
                    step_name=step.name,
                )

                if state.debug_mode == DebugMode.ALL:
                    label = f"{step.name}_{field_def.data_key}"
                    await self._take_debug_screenshot(page=page, label=label, state=state)
            except CrawlerError as e:
                if strict:
                    raise
                self._logger.warning(
                    f"Field failed (non-strict): selector='{field_def.selector}' step='{step.name}' error={e}"
                )

        if step.post_field_extraction is not None:
            await self._extract_step_data(
                page=page,
                extractions=step.post_field_extraction,
                step_name=step.name,
                state=state,
            )

        try:
            executor = get_action_executor(action_type=step.next_action.type, step_name=step.name)
            await executor.execute(
                page=page,
                action=step.next_action,
                step_name=step.name,
                input_data=input_data,
            )

            if state.debug_mode == DebugMode.ALL:
                await self._take_debug_screenshot(page=page, label=f"{step.name}_after_action", state=state)
        except CrawlerError as e:
            if strict:
                raise
            self._logger.warning(
                f"Action failed (non-strict): action='{step.next_action.type}' step='{step.name}' error={e}"
            )

        self._logger.info(f"Step completed: name='{step.name}'")

    async def _capture_final_page(
        self,
        page: Page,
        instructions: Instructions,
        steps_completed: int,
        url: str,
        input_data: dict[str, Any],
        raw_instructions: dict[str, Any],
        state: _CrawlState,
        strict: bool,
    ) -> CrawlResult | InMemoryCrawlResult:
        final_page = instructions.final_page

        try:
            await page.wait_for_selector(
                selector=final_page.wait_for,
                state="visible",
                timeout=final_page.timeout_ms,
            )
            self._logger.info(f"Final page loaded: selector='{final_page.wait_for}'")
        except (PlaywrightTimeoutError, PlaywrightError) as e:
            if strict:
                raise CrawlerTimeoutError(
                    selector=final_page.wait_for,
                    step_name="final_page",
                    timeout_ms=final_page.timeout_ms,
                ) from e
            self._logger.warning(f"Final page wait timeout (non-strict): selector='{final_page.wait_for}'")

        if final_page.post_wait_delay_ms > 0:
            self._logger.info(f"Waiting for SPA content to render: delay_ms={final_page.post_wait_delay_ms}")
            await page.wait_for_timeout(final_page.post_wait_delay_ms)

        if state.debug_mode in (DebugMode.END, DebugMode.ALL):
            await self._take_debug_screenshot(page=page, label="end", state=state)

        html_content = await page.content()
        final_url = page.url

        extracted_data: dict[str, Any] = dict(state.extracted_data)
        if instructions.data_extraction is not None:
            final_page_data = await extract_data(
                page=page,
                config=instructions.data_extraction,
            )
            extracted_data.update(final_page_data)
            self._logger.info(f"Final page extraction complete: fields_extracted={len(final_page_data)}")
        self._logger.info(f"Total extracted data: fields={len(extracted_data)}")

        if state.output_dir is not None:
            html_path = state.output_dir / "result.html"
            html_path.write_text(data=html_content, encoding="utf-8")
            self._logger.info(f"Saved HTML: path='{html_path}'")

            screenshot_path = state.output_dir / "result.png"
            if final_page.screenshot_selector:
                locator = page.locator(final_page.screenshot_selector)
                await locator.screenshot(path=str(screenshot_path))
            else:
                await page.screenshot(path=str(screenshot_path), full_page=True)
            self._logger.info(f"Saved screenshot: path='{screenshot_path}'")

            return CrawlResult(
                html_path=html_path,
                screenshot_path=screenshot_path,
                final_url=final_url,
                steps_completed=steps_completed,
                extracted_data=extracted_data,
            )

        if state.debug_mode != DebugMode.NONE:
            if final_page.screenshot_selector:
                locator = page.locator(final_page.screenshot_selector)
                final_screenshot = await locator.screenshot()
            else:
                final_screenshot = await page.screenshot(full_page=True)

            state.in_memory_screenshots.append(final_screenshot)
            self._logger.info("Captured final screenshot in-memory")

        return InMemoryCrawlResult(
            url=url,
            input_data=input_data,
            instructions=raw_instructions,
            screenshots=state.in_memory_screenshots,
            html=html_content,
            final_url=final_url,
            steps_completed=steps_completed,
            extracted_data=extracted_data,
        )
