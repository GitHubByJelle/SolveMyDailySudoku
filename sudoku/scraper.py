from .utils import logger
from dataclasses import dataclass
from datetime import date
from typing import Tuple, Optional, Dict, Any
from fake_useragent import UserAgent
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import time
import traceback
from pathlib import Path

ua = UserAgent()

@dataclass
class SudokuInfo:
    id: str                         # The id of the daily problem
    mission: str                    # The string representing the sudoku puzzle (0 for empty cells)
    solution: str                   # Solution for the sudoku puzzle
    win_rate: float                 # Win rate for users
    difficulty: str                 # Difficulty assigned by sudoku.com

class SudokoScraper:
    """
    Scrapes the daily Sudoku JSON via the site's own API call.
    Each fetch spins up a fresh headless Chromium, navigates to the page
    to obtain cookies/headers, then either captures the site's API call
    or calls the endpoint inside the browser context.
    """

    def __init__(
        self,
        headless: bool = True,
        user_agent: Optional[str] = ua.random,
        locale: str = "en-US",
        page_url: str = "https://sudoku.com/challenges/daily-sudoku",
        api_base: str = "https://sudoku.com/api/dc",
        api_version: str = "v=2",
        wait_until: str = "domcontentloaded",
        wait_timeout_ms: int = 10_000,
    ):
        self.headless = headless
        self.user_agent = user_agent
        self.locale = locale
        self.page_url = page_url
        self.api_base = api_base.rstrip("/")
        self.api_version = api_version
        self.wait_until = wait_until
        self.wait_timeout_ms = wait_timeout_ms

    def _build_api_url(self, y: int, m: int, d: int) -> str:
        # No leading zeros for month/day, matching the site pattern
        return f"{self.api_base}/{y}-{m}-{d}?{self.api_version}"

    def fetch_for_date(self, y: int, m: int, d: int) -> Tuple[str, Dict[str, Any]]:
        """Fetch the Sudoku JSON for a specific date (YYYY, M, D)."""
        target = self._build_api_url(y, m, d)
        logger.info("Fetching Sudoku for date %04d-%02d-%02d", y, m, d)
        logger.debug("Target API URL: %s", target)

        with sync_playwright() as p:
            browser = None
            try:
                logger.info("Launching Chromium (headless=%s)", self.headless)
                browser = p.chromium.launch(headless=self.headless)

                logger.info("Creating browser context (UA=%s, locale=%s)", self.user_agent, self.locale)
                context = browser.new_context(
                    user_agent=self.user_agent,
                    locale=self.locale,
                )
                page = context.new_page()

                logger.info("Navigating to %s (wait_until=%s)", self.page_url, self.wait_until)
                page.goto(self.page_url, wait_until=self.wait_until)

                # Option A: capture site's own API call
                try:
                    logger.info("Waiting for API response (timeout=%dms)", self.wait_timeout_ms)
                    resp = page.wait_for_response(
                        lambda r: r.url.startswith(f"{self.api_base}/") and self.api_version in r.url,
                        timeout=self.wait_timeout_ms
                    )
                    called_url = resp.url
                    logger.info("Captured API call: %s", called_url)
                    data = resp.json()
                    logger.debug("Received JSON payload with keys: %s", list(data.keys()))
                except Exception as e:
                    logger.warning("Failed to capture API call directly (%s). Falling back to manual fetch.", e)
                    called_url = target
                    logger.info("Calling API inside browser context: %s", called_url)
                    data = page.evaluate(
                        """async (url) => {
                            const res = await fetch(url, { credentials: 'include' });
                            if (!res.ok) throw new Error(`Status ${res.status}`);
                            return res.json();
                        }""",
                        target
                    )
                    logger.debug("Received JSON payload with keys: %s", list(data.keys()))

                logger.info("Successfully fetched Sudoku data for %04d-%02d-%02d", y, m, d)
                return called_url, data

            except Exception as e:
                logger.error("Error while fetching Sudoku for %04d-%02d-%02d", y, m, d)
                logger.error("Exception: %s: %s", type(e).__name__, e)
                logger.debug("Full traceback:\n%s", traceback.format_exc())
                raise
            finally:
                if browser:
                    logger.info("Closing browser")
                    browser.close()
                    logger.info("Browser closed")

    def fetch_daily(self) -> Tuple[str, Dict[str, Any]]:
        """Fetch today's Sudoku JSON."""
        t = date.today()
        _, json_payload = self.fetch_for_date(t.year, t.month, t.day)
        return SudokuInfo(**json_payload)
    
    def fill_in_answer(
        self,
        info: Optional[SudokuInfo] = None,
        *,
        solution: Optional[str] = None,
        keep_open: bool = False,
        screenshot_on_error: Path = Path("sudoku_error.png"),
        cookie_accept_selector: str = "#onetrust-accept-btn-handler",
        board_selector: str = "#game canvas",
    ) -> None:
        """
        Open the daily Sudoku page and fill in the provided solution.

        Args:
            info: SudokuInfo containing the solved grid (preferred).
            solution: Raw 81-char solution string (digits 1-9). If provided, overrides info.solution.
            keep_open: If True and not headless, waits for Enter before closing the browser.
            screenshot_on_error: Path to save a full-page screenshot if anything fails.
            cookie_accept_selector: Selector for the OneTrust cookie accept button.
            board_selector: Selector for the board canvas.

        Raises:
            Any exception encountered will be logged (with traceback), a screenshot attempted,
            and then re-raised.
        """
        # Resolve the solution string
        if solution is None:
            if info is None or not getattr(info, "solution", None):
                raise ValueError("No solution provided. Pass a SudokuInfo with .solution or a raw solution string.")
            solution = info.solution

        if len(solution) != 81 or any(ch not in "123456789" for ch in solution):
            raise ValueError("Solution must be an 81-character string of digits 1-9.")

        with sync_playwright() as p:
            browser = None
            page = None
            try:
                logger.info("Launching Chromium (headless=%s)", self.headless)
                browser = p.chromium.launch(headless=self.headless)

                logger.info("Creating browser context (UA=%s, locale=%s)", self.user_agent, self.locale)
                context = browser.new_context(user_agent=self.user_agent, locale=self.locale)

                logger.info("Opening new page")
                page = context.new_page()

                logger.info("Navigating to %s (wait_until=%s)", self.page_url, self.wait_until)
                page.goto(self.page_url, wait_until=self.wait_until)

                # Accept cookies (OneTrust), if present
                try:
                    logger.info("Checking for cookie banner")
                    page.wait_for_selector(cookie_accept_selector, state="visible", timeout=10_000)
                    page.locator(cookie_accept_selector).click()
                    logger.info("Cookies accepted")
                except PWTimeoutError:
                    logger.info("Cookie banner not found or already accepted")

                # Wait for the board canvas
                logger.info("Waiting for the Sudoku canvas to be visible")
                board = page.locator(board_selector)
                board.wait_for(state="visible", timeout=10_000)

                logger.info("Reading canvas bounding box")
                box = board.bounding_box()
                if not box:
                    raise RuntimeError("Couldn't get canvas bounding box")

                logger.info("Canvas box: %s", box)
                cell_w = box["width"] / 9.0
                cell_h = box["height"] / 9.0

                # Focus the game (first cell)
                logger.info("Focusing the board")
                page.mouse.click(box["x"] + cell_w * 0.5, box["y"] + cell_h * 0.5)
                time.sleep(0.1)

                # Fill all 81 cells in row-major order
                logger.info("Starting to fill 81 cells")
                idx = 0
                for r in range(9):
                    for c in range(9):
                        x = box["x"] + c * cell_w + cell_w / 2
                        y = box["y"] + r * cell_h + cell_h / 2
                        digit = solution[idx]

                        page.mouse.click(x, y)
                        time.sleep(0.01)  # tiny delay helps with UI animations
                        page.keyboard.type(digit)

                        idx += 1

                logger.info("Filling complete")

                if keep_open and not self.headless:
                    input("Done. Press Enter to close...")

            except (PWTimeoutError, Exception) as e:
                # Try to screenshot for diagnostics
                try:
                    if page:
                        page.screenshot(path=str(screenshot_on_error), full_page=True)
                        logger.error("Saved error screenshot to %s", screenshot_on_error.resolve())
                except Exception as ss_e:
                    logger.warning("Failed to take screenshot: %s", ss_e)

                logger.error("Error encountered during Sudoku automation")
                logger.error("Exception: %s: %s", type(e).__name__, e)
                logger.debug("Full traceback:\n%s", traceback.format_exc())
                raise
            finally:
                if browser:
                    logger.info("Closing browser")
                    browser.close()
                    logger.info("Browser closed")


if __name__ == "__main__":
    scraper = SudokoScraper(headless=False)  # set False to watch it type
    info = scraper.fetch_daily()             # returns SudokuInfo
    print(info)
    scraper.fill_in_answer(info=info, keep_open=True)