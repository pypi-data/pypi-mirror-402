import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import time
import requests
from bs4 import BeautifulSoup
from pipeline_node_agents.core.logging_config import get_logger
from pipeline_node_agents.core.logger_bootstrap import init_pipeline_logger

logger = get_logger(__name__)


class Scraper:
    @staticmethod
    def extract_urls(search_results: list) -> dict:
        """Extract the first URL from search results."""
        if search_results and len(search_results) > 0:
            return {"search_results_urls": [result["url"] for result in search_results]}
        raise ValueError("No search results to extract URL from")


    @staticmethod
    def _scrape_url(url: str, timeout: int = 10, max_attempts: int = 5) -> str:
        """
        Scrape textual content from a website with retries.

        Returns:
            { "page_content": str }
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; NodeAgents007/1.0)"
        }

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")

                for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
                    tag.decompose()

                text = soup.get_text(separator=" ", strip=True)
                text = " ".join(text.split())

                return text

            except Exception as e:
                logger.warning(f"Attempt {attempt}/{max_attempts} failed: {e}")
                time.sleep(1)

        raise RuntimeError(f"Failed to scrape {url} after {max_attempts} attempts")
    
    @staticmethod
    def scrape(search_results: list, timeout: int = 10, max_attempts: int = 5, max_urls: int = 5) -> dict:
        search_results_urls = Scraper.extract_urls(search_results)["search_results_urls"]
        max_urls = min(max_urls, len(search_results_urls))
        for url in search_results_urls[:max_urls]:
            try:
                return Scraper._scrape_url(url, timeout, max_attempts)
            except Exception as e:
                logger.warning(f"Failed to scrape {url}: \n{e},\n going to next URL...")
        raise RuntimeError(f"Failed to scrape urls {search_results_urls[:max_urls]} after {max_attempts} attempts")



if __name__ == "__main__":
    def main():
        init_pipeline_logger(pipeline_name="scraper_test")

        search_results = [{"name": "AMC Theatres", "url": "https://www.amctheatres.com/movies"}, {"name": "Web scraping", "url": "https://en.wikipedia.org/wiki/Web_scraping"}]
        result = Scraper.scrape(search_results)

        logger.info(result[:1000] + "...")

    main()