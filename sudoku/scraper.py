from dataclasses import dataclass
from datetime import date
from typing import Tuple, Optional, Dict, Any
from fake_useragent import UserAgent
from playwright.sync_api import sync_playwright

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
        wait_until: str = "networkidle",
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

        # spin up playwright and make sure we always close resources
        with sync_playwright() as p:
            browser = None
            try:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=self.user_agent,
                    locale=self.locale,
                )
                page = context.new_page()

                # Let cookies/session/anti-bot checks happen
                page.goto(self.page_url, wait_until=self.wait_until)

                # Option A: capture site's own API call
                try:
                    resp = page.wait_for_response(
                        lambda r: r.url.startswith(f"{self.api_base}/") and self.api_version in r.url,
                        timeout=self.wait_timeout_ms
                    )
                    called_url = resp.url
                    data = resp.json()
                except Exception:
                    # Option B: call the endpoint yourself *inside* the browser context
                    called_url = target
                    data = page.evaluate(
                        """async (url) => {
                            const res = await fetch(url, { credentials: 'include' });
                            if (!res.ok) throw new Error(`Status ${res.status}`);
                            return res.json();
                        }""",
                        target
                    )

                return called_url, data

            finally:
                if browser:
                    browser.close()

    def fetch_daily(self) -> Tuple[str, Dict[str, Any]]:
        """Fetch today's Sudoku JSON."""
        t = date.today()
        _, json_payload = self.fetch_for_date(t.year, t.month, t.day)
        return SudokuInfo(**json_payload)


if __name__ == "__main__":
    scraper = SudokoScraper()
    info = scraper.fetch_daily()
    print(info)