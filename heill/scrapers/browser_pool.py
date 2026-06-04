"""
Async Playwright browser pool — up to POOL_SIZE concurrent contexts.
Call start_pool() at app startup and stop_pool() on shutdown.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

logger = logging.getLogger(__name__)

POOL_SIZE = 3

_browsers: list = []
_semaphore: asyncio.Semaphore | None = None
_playwright = None


async def start_pool() -> None:
    global _playwright, _browsers, _semaphore
    try:
        from playwright.async_api import async_playwright

        _semaphore = asyncio.Semaphore(POOL_SIZE)
        _playwright = await async_playwright().start()
        for _ in range(POOL_SIZE):
            browser = await _playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            _browsers.append(browser)
        logger.info("Browser pool started (%d instances)", POOL_SIZE)
    except Exception as exc:
        logger.warning("Could not start browser pool: %s — Playwright tier disabled", exc)


async def stop_pool() -> None:
    global _playwright, _browsers
    for browser in _browsers:
        try:
            await browser.close()
        except Exception:
            pass
    _browsers = []
    if _playwright:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None
    logger.info("Browser pool stopped")


@asynccontextmanager
async def acquire_page(timeout_ms: int = 30_000) -> AsyncIterator:
    """Acquire a browser page from the pool."""
    if not _browsers:
        raise RuntimeError("Browser pool not available")

    assert _semaphore is not None
    async with _semaphore:
        browser = _browsers[0]
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        page.set_default_timeout(timeout_ms)
        try:
            yield page
        finally:
            await context.close()


async def fetch_with_browser(url: str, wait_for: str = "networkidle") -> str:
    """Fetch a URL with a headless browser; returns rendered HTML."""
    async with acquire_page() as page:
        await page.goto(url, wait_until=wait_for)
        return await page.content()
