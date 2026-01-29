"""
Utility functions for the crawler framework.

Date formatting, selector utilities, and other helper functions.
"""

import logging
from datetime import datetime

from .config import CSS_ATTRIBUTE_VALUE_ESCAPE_CHARS, CSS_SELECTOR_ESCAPE_CHARS
from .exceptions import InvalidInstructionError


def setup_logger(name: str) -> logging.Logger:
    """Create a structured logger for the crawler framework."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def format_date(value: str, target_format: str) -> str:
    """
    Convert a date string to the target format.

    Input format is expected to be ISO 8601 (YYYY-MM-DD).
    Target format uses strftime directives mapped from common patterns.

    Args:
        value: Date string in ISO 8601 format (YYYY-MM-DD)
        target_format: Target format pattern (e.g., "DD.MM.YYYY", "MM/DD/YYYY")

    Returns:
        Formatted date string

    """
    # Using naive datetime intentionally - we're only converting date formats, not handling timezones
    input_date = datetime.strptime(value, "%Y-%m-%d")  # noqa: DTZ007

    format_mapping: dict[str, str] = {
        "DD.MM.YYYY": "%d.%m.%Y",
        "MM/DD/YYYY": "%m/%d/%Y",
        "YYYY-MM-DD": "%Y-%m-%d",
        "DD/MM/YYYY": "%d/%m/%Y",
        "YYYY/MM/DD": "%Y/%m/%d",
        "DD-MM-YYYY": "%d-%m-%Y",
        "MM-DD-YYYY": "%m-%d-%Y",
    }

    strftime_format = format_mapping.get(target_format)
    if strftime_format is None:
        msg = f"Unsupported date format: {target_format}"
        raise InvalidInstructionError(msg)

    return input_date.strftime(strftime_format)


def normalize_selector(selector: str) -> str:
    """
    Normalize a CSS selector for consistent usage.

    Strips whitespace and validates basic selector syntax.

    Args:
        selector: CSS selector string

    Returns:
        Normalized selector string

    """
    normalized = selector.strip()
    if not normalized:
        msg = "Empty selector provided"
        raise InvalidInstructionError(msg)
    return normalized


def escape_css_id(element_id: str) -> str:
    """
    Escape special characters in CSS ID selectors.

    Characters like :, [], (), etc. need backslash escaping.

    Args:
        element_id: Raw element ID

    Returns:
        Escaped ID safe for use in CSS selectors

    """
    return "".join("\\" + char if char in CSS_SELECTOR_ESCAPE_CHARS else char for char in element_id)


def escape_css_attribute_value(value: str) -> str:
    """
    Escape special characters in CSS attribute selector values.

    Handles quotes, backslashes, and bracket characters that could break
    attribute selectors like [data-cy='value'].

    Args:
        value: Raw value to use in attribute selector

    Returns:
        Escaped value safe for use in CSS attribute selectors

    """
    return "".join("\\" + char if char in CSS_ATTRIBUTE_VALUE_ESCAPE_CHARS else char for char in value)


def interpolate_selector_value(selector: str, value: str) -> str:
    """
    Safely interpolate a value into a selector placeholder.

    Replaces ${value} placeholder with an escaped version of the value.

    Args:
        selector: Selector template containing ${value} placeholder
        value: Value to interpolate

    Returns:
        Selector with value safely interpolated

    """
    escaped_value = escape_css_attribute_value(str(value))
    return selector.replace("${value}", escaped_value)
