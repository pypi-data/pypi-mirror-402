"""CAPTCHA detection and handling utilities for WhoCitedMe.

This module provides functions to detect and wait for CAPTCHA resolution
when scraping Google Scholar.
"""

import time
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver


def check_and_wait_captcha(
    driver: WebDriver,
    post_captcha_sleep: tuple[float, float] = (2.0, 4.0),
) -> bool:
    """
    Check for CAPTCHA on the current page and wait for user to solve it.

    This function detects Google reCAPTCHA or Google Scholar's custom CAPTCHA
    and blocks until the user solves it manually in the browser window.

    Args:
        driver: Selenium WebDriver instance.
        post_captcha_sleep: (min, max) seconds to sleep after CAPTCHA is solved.

    Returns:
        True if CAPTCHA was detected and solved, False if no CAPTCHA was found.
    """
    import random

    page_source = driver.page_source

    if "recaptcha" in page_source or "gs_captcha_c" in page_source:
        print("\n⚠️  CAPTCHA detected! Please solve it in the browser window...")

        input("Press Enter after you have solved the CAPTCHA...")

        print("✅ CAPTCHA solved. Resuming...")
        time.sleep(random.uniform(*post_captcha_sleep))
        return True

    return False


def random_sleep(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    Sleep for a random duration to simulate human behavior.

    Args:
        min_seconds: Minimum sleep duration.
        max_seconds: Maximum sleep duration.
    """
    import random

    time.sleep(random.uniform(min_seconds, max_seconds))
