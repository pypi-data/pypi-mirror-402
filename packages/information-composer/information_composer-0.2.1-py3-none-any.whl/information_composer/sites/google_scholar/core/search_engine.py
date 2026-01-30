"""Search engine component for Google Scholar crawler."""

import asyncio
import logging
import random
import time
from typing import Any
from urllib.parse import urlencode  # quote_plus unused

# import aiohttp  # Unused import
from bs4 import BeautifulSoup
import requests

from ..models import SearchConfig, SearchStrategy
from ..utils.rate_limiter import RateLimiter
from ..utils.user_agents import get_random_user_agent


logger = logging.getLogger(__name__)


class SearchEngine:
    """Google Scholar search engine with multiple strategies."""

    def __init__(self, config: SearchConfig):
        """Initialize search engine with configuration."""
        self.config = config
        self.rate_limiter = RateLimiter(rate_limit=config.rate_limit)
        self.session: requests.Session | None = None
        self._setup_session()

    def _setup_session(self) -> None:
        """Setup requests session with appropriate headers."""
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": get_random_user_agent()
                if self.config.user_agent_rotation
                else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

    def _build_search_url(self, query: str, start: int = 0) -> str:
        """Build Google Scholar search URL with parameters."""
        base_url = "https://scholar.google.com/scholar"
        params = {
            "q": query,
            "hl": self.config.language,
            "start": start,
        }
        # Add year range if specified
        if self.config.year_range:
            start_year, end_year = self.config.year_range
            params["as_ylo"] = start_year
            params["as_yhi"] = end_year
        # Add sorting
        if self.config.sort_by == "date":
            params["scisbd"] = "1"
        # Exclude patents if requested
        if not self.config.include_patents:
            params["as_vis"] = "1"
        return f"{base_url}?{urlencode(params)}"

    def _extract_scholar_id(self, url: str) -> str | None:
        """Extract Google Scholar ID from URL."""
        try:
            # Extract from various URL patterns
            if "cluster=" in url:
                return url.split("cluster=")[1].split("&")[0]
            elif "/citations" in url:
                return url.split("user=")[1].split("&")[0] if "user=" in url else None
            return None
        except Exception:
            return None

    async def search_requests(
        self, query: str
    ) -> tuple[list[BeautifulSoup | dict], dict]:
        """Search using requests library."""
        results: list[BeautifulSoup | dict | Any] = []
        metadata = {"strategy": "requests", "total_fetched": 0}
        try:
            current_start = 0
            fetched_count = 0
            while fetched_count < self.config.max_results:
                await self.rate_limiter.acquire()
                url = self._build_search_url(query, current_start)
                logger.debug(f"Fetching URL: {url}")
                # Rotate user agent if enabled
                if self.session and self.config.user_agent_rotation:
                    self.session.headers["User-Agent"] = get_random_user_agent()
                if not self.session:
                    raise RuntimeError("Session not initialized")
                response = self.session.get(
                    url, timeout=self.config.timeout, allow_redirects=True
                )
                if response.status_code == 429:
                    logger.warning("Rate limited, switching to Selenium strategy")
                    metadata["rate_limited"] = True
                    break
                elif response.status_code == 403:
                    logger.warning("Access forbidden, switching to Selenium strategy")
                    metadata["blocked"] = True
                    break
                elif response.status_code != 200:
                    logger.error(f"HTTP error: {response.status_code}")
                    break
                soup = BeautifulSoup(response.content, "html.parser")
                # Check for CAPTCHA or blocking
                if self._is_blocked(soup):
                    logger.warning("Blocked by Google Scholar, switching strategy")
                    metadata["blocked"] = True
                    break
                # Extract paper elements
                paper_elements = soup.find_all(
                    "div", class_="gs_r gs_or gs_scl"
                ) or soup.find_all("div", class_="gs_ri")
                if not paper_elements:
                    logger.info("No more results found")
                    break
                results.extend(paper_elements)
                fetched_count += len(paper_elements)
                current_start += len(paper_elements)
                # Check if we've reached the end
                if len(paper_elements) < 10:  # Google Scholar usually shows 10 per page
                    break
                metadata["total_fetched"] = fetched_count
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            metadata["error"] = str(e)
        except Exception as e:
            logger.error(f"Unexpected error in requests search: {e}")
            metadata["error"] = str(e)
        return results, metadata

    def _is_blocked(self, soup: BeautifulSoup) -> bool:
        """Check if the response indicates blocking or CAPTCHA."""
        # Check for CAPTCHA
        if soup.find("div", id="captcha-form"):
            return True
        # Check for blocking messages
        text = soup.get_text().lower()
        blocking_indicators = [
            "unusual traffic",
            "captcha",
            "blocked",
            "automation",
            "robot",
        ]
        return any(indicator in text for indicator in blocking_indicators)

    async def search_selenium(
        self, query: str
    ) -> tuple[list[BeautifulSoup | dict], dict]:
        """Search using Selenium WebDriver."""
        results: list[BeautifulSoup | dict | Any] = []
        metadata = {"strategy": "selenium", "total_fetched": 0}
        try:
            # Import selenium here to make it optional
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait

            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            if self.config.user_agent_rotation:
                chrome_options.add_argument(f"--user-agent={get_random_user_agent()}")
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 10)
            try:
                current_start = 0
                fetched_count = 0
                while fetched_count < self.config.max_results:
                    await self.rate_limiter.acquire()
                    url = self._build_search_url(query, current_start)
                    logger.debug(f"Selenium fetching URL: {url}")
                    driver.get(url)
                    # Wait for results to load
                    try:
                        wait.until(
                            EC.presence_of_element_located((By.CLASS_NAME, "gs_ri"))
                        )
                    except Exception:
                        logger.warning("No results found or page failed to load")
                        break
                    # Check for CAPTCHA
                    if driver.find_elements(By.ID, "captcha-form"):
                        logger.warning("CAPTCHA detected in Selenium")
                        metadata["captcha"] = True
                        break
                    # Get page source and parse
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    paper_elements = soup.find_all("div", class_="gs_ri")
                    if not paper_elements:
                        break
                    results.extend(paper_elements)
                    fetched_count += len(paper_elements)
                    current_start += len(paper_elements)
                    if len(paper_elements) < 10:
                        break
                    metadata["total_fetched"] = fetched_count
                    # Random delay to appear more human-like
                    await asyncio.sleep(random.uniform(1, 3))
            finally:
                driver.quit()
        except ImportError:
            logger.error("Selenium not available, please install: pip install selenium")
            metadata["error"] = "Selenium not installed"
        except Exception as e:
            logger.error(f"Selenium search error: {e}")
            metadata["error"] = str(e)
        return results, metadata

    async def search_scholarly(
        self, query: str
    ) -> tuple[list[BeautifulSoup | dict], dict]:
        """Search using scholarly library as fallback."""
        results: list[BeautifulSoup | dict | Any] = []
        metadata = {"strategy": "scholarly", "total_fetched": 0}
        try:
            # Import scholarly here to make it optional
            from scholarly import scholarly

            search_query = scholarly.search_pubs(query)
            for fetched_count, publication in enumerate(search_query):
                if fetched_count >= self.config.max_results:
                    break
                results.append(publication)
                metadata["total_fetched"] = fetched_count + 1
                # Rate limiting
                await asyncio.sleep(self.config.rate_limit)
        except ImportError:
            logger.error(
                "Scholarly not available, please install: pip install scholarly"
            )
            metadata["error"] = "Scholarly not installed"
        except Exception as e:
            logger.error(f"Scholarly search error: {e}")
            metadata["error"] = str(e)
        return results, metadata

    async def search(self, query: str) -> tuple[list, dict]:
        """
        Execute search using configured strategy with fallbacks.
        Returns:
            Tuple of (results, metadata)
        """
        logger.info(f"Searching for: {query}")
        start_time = time.time()
        # Try primary strategy
        results: list[BeautifulSoup | dict | Any] = []
        metadata: dict = {}
        if self.config.search_strategy == SearchStrategy.REQUESTS:
            results, metadata = await self.search_requests(query)
        elif self.config.search_strategy == SearchStrategy.SELENIUM:
            results, metadata = await self.search_selenium(query)
        elif self.config.search_strategy == SearchStrategy.SCHOLARLY:
            results, metadata = await self.search_scholarly(query)
        else:
            # This should never happen due to enum validation, but provide fallback
            logger.warning(
                f"Unknown search strategy: {self.config.search_strategy}, falling back to requests"
            )
            results, metadata = await self.search_requests(query)
        # Try fallback strategies if primary failed
        if not results and "error" in metadata:
            logger.info("Primary strategy failed, trying fallbacks")
            if (
                self.config.use_selenium_fallback
                and self.config.search_strategy != SearchStrategy.SELENIUM
            ):
                logger.info("Trying Selenium fallback")
                fallback_results, fallback_metadata = await self.search_selenium(query)
                if fallback_results:
                    results = fallback_results
                    metadata.update(fallback_metadata)
                    metadata["used_fallback"] = "selenium"
            # Try scholarly as last resort
            if not results and self.config.search_strategy != SearchStrategy.SCHOLARLY:
                logger.info("Trying scholarly fallback")
                fallback_results, fallback_metadata = await self.search_scholarly(query)
                if fallback_results:
                    results = fallback_results
                    metadata.update(fallback_metadata)
                    metadata["used_fallback"] = "scholarly"
        metadata["search_time"] = time.time() - start_time
        metadata["query"] = query
        logger.info(
            f"Search completed in {metadata['search_time']:.2f}s, found {len(results)} results"
        )
        return results, metadata

    def close(self) -> None:
        """Close the session and cleanup."""
        if self.session:
            self.session.close()
