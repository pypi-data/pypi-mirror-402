"""Browser driver utilities for WhoCitedMe.

This module provides functions to create and configure Chrome drivers
for web scraping, including both standard and undetected versions.
"""

import ssl
import time
from typing import Optional

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Ignore SSL certificate errors
ssl._create_default_https_context = ssl._create_unverified_context


def create_chrome_driver(
    headless: bool = False,
    incognito: bool = True,
    window_size: str = "1920,1080",
    disable_extensions: bool = True,
) -> webdriver.Chrome:
    """
    Create a standard Chrome WebDriver with anti-detection configurations.

    Args:
        headless: Run Chrome in headless mode.
        incognito: Run Chrome in incognito mode.
        window_size: Browser window size in "width,height" format.
        disable_extensions: Disable browser extensions.

    Returns:
        Configured Chrome WebDriver instance.
    """
    options = Options()

    if incognito:
        options.add_argument("--incognito")
    if headless:
        options.add_argument("--headless=new")

    options.add_argument(f"--window-size={window_size}")

    if disable_extensions:
        options.add_argument("--disable-extensions")

    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")

    # Anti-detection configurations
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    print("Starting Chrome (standard mode)...")
    driver = webdriver.Chrome(options=options)
    time.sleep(2)
    print("Chrome (standard mode) started.")

    return driver


def create_undetected_chrome_driver(
    headless: bool = False,
    incognito: bool = True,
    window_size: str = "1920,1080",
    disable_extensions: bool = True,
    use_subprocess: bool = True,
) -> uc.Chrome:
    """
    Create an undetected Chrome WebDriver that bypasses bot detection.

    This driver is more suitable for scraping sites with strict bot detection
    like Google Scholar.

    Args:
        headless: Run Chrome in headless mode.
        incognito: Run Chrome in incognito mode.
        window_size: Browser window size in "width,height" format.
        disable_extensions: Disable browser extensions.
        use_subprocess: Use subprocess mode to avoid process conflicts.

    Returns:
        Configured undetected Chrome WebDriver instance.
    """
    options = uc.ChromeOptions()

    if incognito:
        options.add_argument("--incognito")
    if headless:
        options.add_argument("--headless=new")

    options.add_argument(f"--window-size={window_size}")

    if disable_extensions:
        options.add_argument("--disable-extensions")

    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")

    print("Starting Chrome (undetected mode)...")
    driver = uc.Chrome(options=options, use_subprocess=use_subprocess)
    time.sleep(2)
    print("Chrome (undetected mode) started.")

    return driver
