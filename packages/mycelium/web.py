import os
import traceback
from urllib.parse import urlparse

import httpx
from loguru import logger
from tavily import AsyncTavilyClient

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
USE_SCRAPER_API_KEY = os.getenv("USE_SCRAPER_API_KEY")
USE_SCRAPER_TIMEOUT = 60


def trim_url(url):
    parsed_url = urlparse(url)
    queryless_url = parsed_url._replace(query="")
    fragmentless_url = queryless_url._replace(fragment="")
    trimmed_url = fragmentless_url.geturl()
    return trimmed_url


async def search(search_query):
    try:
        logger.info(f"executing search: {search_query}")
        tavily_client = AsyncTavilyClient(api_key=TAVILY_API_KEY)
        response = await tavily_client.search(search_query)
        search_result = response.get("results")
        urls = [result.get("url") for result in search_result]
        logger.info(f"search results: {urls}")
        return urls
    except KeyboardInterrupt:
        raise
    except Exception as error:
        logger.error(f"search for {search_query} failed with error: {error}\n{traceback.format_exc()}")
        return []


async def scrape(url):
    try:
        async with httpx.AsyncClient(timeout=USE_SCRAPER_TIMEOUT) as client:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {USE_SCRAPER_API_KEY}"
            }
            payload = {
                "format": "markdown",
                "advanced_proxy": False,
                "url": url
            }
            response = await client.post(u"https://api.usescraper.com/scraper/scrape", headers=headers, json=payload)
            if "application/json" not in response.headers.get("content-type"):
                logger.warning(f"no json in response for {url}: {response.text}")
                return None
            response_json = response.json()
            if response_json.get("status") != "scraped":
                logger.warning(f"scrape failed for {url}: {response.text}")
                return None
            return response_json.get("text")
    except KeyboardInterrupt:
        raise
    except Exception as error:
        logger.warning(f"scrape for {scrape} failed with error: {error}\n{traceback.format_exc()}")
        return None
