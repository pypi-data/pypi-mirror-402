"""Web Search Tools - Python @tool decorated functions

Provides web search capabilities with Google (primary) and DuckDuckGo (fallback).

Based on proven implementation from Lumentor project.

Usage:
    from tools.search_tools import web_search

    result = await web_search.ainvoke({"query": "python tutorials", "num_results": 5})
    if result["provider"] == "duckduckgo":
        print("Using fallback provider")
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import List, Tuple

import httpx
import trafilatura
from langchain_core.tools import tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_google_community.search import GoogleSearchAPIWrapper

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str


class RateLimiter:
    """Simple async rate limiter using time-based delays."""

    def __init__(self, requests_per_second: float):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second (e.g., 0.5 = 1 req per 2 seconds)
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    async def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_interval:
            wait_time = self.min_interval - time_since_last_request
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()


class GoogleSearchProvider:
    """Google Programmable Search Engine implementation with rate limiting."""

    def __init__(self):
        """
        Initialize Google Search provider.

        Raises:
            ValueError: If GOOGLE_API_KEY or GOOGLE_CSE_ID are not set
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        cse_id = os.getenv("GOOGLE_CSE_ID")

        logger.info(f"Google Search credentials check - API Key: {bool(api_key)}, CSE ID: {bool(cse_id)}")

        if not api_key or not cse_id:
            raise ValueError(
                "Google Search requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables"
            )

        try:
            self.search_wrapper = GoogleSearchAPIWrapper(
                google_api_key=api_key,
                google_cse_id=cse_id
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Search wrapper: {e}")
            raise ValueError(f"Failed to initialize Google Search: {e}")

        # Rate limiter: configurable (default 1 request per second)
        self.rate_limiter = RateLimiter(
            requests_per_second=float(os.getenv("GOOGLE_SEARCH_RATE_LIMIT", "1.0"))
        )
        self.timeout = float(os.getenv("GOOGLE_SEARCH_TIMEOUT", "30.0"))

    async def search(self, query: str, num_results: int) -> List[SearchResult]:
        """
        Perform Google search with rate limiting and timeout.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of SearchResult objects
        """
        logger.debug(f"Performing Google search for query: {query}")
        logger.debug(f"Requested number of results: {num_results}")

        # Apply rate limiting
        await self.rate_limiter.wait()

        try:
            # GoogleSearchAPIWrapper.results() is synchronous, run in thread pool with timeout
            loop = asyncio.get_event_loop()
            raw_results = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.search_wrapper.results(query, num_results=num_results)
                ),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Google search timed out after {self.timeout}s for query: {query}")
            return []
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []

        logger.debug(f"Number of results returned: {len(raw_results)}")

        return [
            SearchResult(
                title=result.get("title", ""),
                url=result.get("link", ""),
                snippet=result.get("snippet", ""),
            )
            for result in raw_results
        ]


class DuckDuckGoSearchProvider:
    """DuckDuckGo search implementation with rate limiting."""

    def __init__(self):
        """Initialize DuckDuckGo Search provider."""
        self.search_wrapper = DuckDuckGoSearchAPIWrapper()

        # Rate limiter: configurable (default 1 request per second)
        self.rate_limiter = RateLimiter(
            requests_per_second=float(os.getenv("DUCKDUCKGO_SEARCH_RATE_LIMIT", "1.0"))
        )
        self.timeout = float(os.getenv("DUCKDUCKGO_SEARCH_TIMEOUT", "30.0"))

    async def search(self, query: str, num_results: int) -> List[SearchResult]:
        """
        Perform DuckDuckGo search with rate limiting and timeout.

        Args:
            query: Search query string
            num_results: Number of results to return

        Returns:
            List of SearchResult objects
        """
        logger.debug(f"Performing DuckDuckGo search for query: {query}")
        logger.debug(f"Requested number of results: {num_results}")

        # Apply rate limiting
        await self.rate_limiter.wait()

        try:
            # DuckDuckGoSearchAPIWrapper.results() is synchronous, run in thread pool with timeout
            loop = asyncio.get_event_loop()
            raw_results = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.search_wrapper.results(query, max_results=num_results)
                ),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"DuckDuckGo search timed out after {self.timeout}s for query: {query}")
            return []
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

        logger.debug(f"Number of results returned: {len(raw_results)}")

        return [
            SearchResult(
                title=result.get("title", ""),
                url=result.get("link", ""),
                snippet=result.get("snippet", ""),
            )
            for result in raw_results
        ]


# Global provider instances (initialized on first use)
_google_provider = None
_duckduckgo_provider = None


async def _web_search_impl(
    query: str,
    num_results: int = 5,
) -> Tuple[List[SearchResult], str, str | None]:
    """
    Internal implementation: Search using Google (preferred) or DuckDuckGo (fallback).

    Returns:
        Tuple of (results, provider_name, error_message_or_none)
    """
    global _google_provider, _duckduckgo_provider

    # Cap num_results at 10 to prevent abuse
    num_results = min(num_results, 10)

    google_error = None
    duckduckgo_error = None

    # Try Google first
    try:
        if _google_provider is None:
            _google_provider = GoogleSearchProvider()

        logger.info(f"Searching with Google: '{query}' ({num_results} results)")
        results = await _google_provider.search(query, num_results)

        if results:
            return results, "google", None
        else:
            logger.warning("Google search returned no results, falling back to DuckDuckGo")
            google_error = "No results returned"

    except ValueError as e:
        # Google credentials not configured - fall back to DuckDuckGo
        google_error = str(e)
        logger.warning(f"Google Search not configured, falling back to DuckDuckGo: {e}")
    except Exception as e:
        # Unexpected error with Google - log and fall back
        google_error = str(e)
        logger.error(f"Google Search failed unexpectedly: {e}", exc_info=True)

    # Fall back to DuckDuckGo
    try:
        if _duckduckgo_provider is None:
            _duckduckgo_provider = DuckDuckGoSearchProvider()

        logger.info(f"Searching with DuckDuckGo: '{query}' ({num_results} results)")
        results = await _duckduckgo_provider.search(query, num_results)

        if results:
            return results, "duckduckgo", None
        else:
            # DuckDuckGo returned empty but didn't error - that's a valid "no results" scenario
            return results, "duckduckgo", None

    except Exception as e:
        duckduckgo_error = str(e)
        logger.error(f"DuckDuckGo Search failed: {e}", exc_info=True)

        # Both providers failed - return error information
        error_msg = f"All search providers failed. Google: {google_error}. DuckDuckGo: {duckduckgo_error}"
        return [], "none", error_msg


@tool
async def web_search(query: str, num_results: int = 5) -> dict:
    """
    Search the web using Google (preferred) or DuckDuckGo (fallback).

    Use this tool when you need to find web pages, articles, documentation,
    or any other information available on the internet.

    Args:
        query: The search query string (e.g., "python async tutorial")
        num_results: Number of results to return (default: 5, max: 10)

    Returns:
        Dictionary with:
        - results: List of {title, url, snippet} objects
        - provider: Which search engine was used ("google", "duckduckgo", or "none" if all failed)
        - query: The original query
        - count: Number of results returned
        - error: (Only present if search failed) Error message explaining what went wrong
    """
    results, provider, error = await _web_search_impl(query, num_results)

    response = {
        "results": [
            {"title": r.title, "url": r.url, "snippet": r.snippet}
            for r in results
        ],
        "provider": provider,
        "query": query,
        "count": len(results),
    }

    if error:
        response["error"] = error

    return response


@tool
async def search_google(query: str, num_results: int = 5) -> dict:
    """
    Search using Google only (no fallback).

    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.
    Use web_search instead if you want automatic fallback to DuckDuckGo.

    Args:
        query: The search query string
        num_results: Number of results to return (default: 5, max: 10)

    Returns:
        Dictionary with results list and metadata, or error if Google not configured
    """
    global _google_provider

    num_results = min(num_results, 10)

    try:
        if _google_provider is None:
            _google_provider = GoogleSearchProvider()

        results = await _google_provider.search(query, num_results)

        return {
            "results": [
                {"title": r.title, "url": r.url, "snippet": r.snippet}
                for r in results
            ],
            "provider": "google",
            "query": query,
            "count": len(results),
        }
    except ValueError as e:
        return {"error": str(e), "provider": "google", "query": query}
    except Exception as e:
        return {"error": f"Google search failed: {e}", "provider": "google", "query": query}


@tool
async def search_duckduckgo(query: str, num_results: int = 5) -> dict:
    """
    Search using DuckDuckGo only.

    No API key required. Good for testing or when Google quota is exhausted.

    Args:
        query: The search query string
        num_results: Number of results to return (default: 5, max: 10)

    Returns:
        Dictionary with results list and metadata
    """
    global _duckduckgo_provider

    num_results = min(num_results, 10)

    try:
        if _duckduckgo_provider is None:
            _duckduckgo_provider = DuckDuckGoSearchProvider()

        results = await _duckduckgo_provider.search(query, num_results)

        return {
            "results": [
                {"title": r.title, "url": r.url, "snippet": r.snippet}
                for r in results
            ],
            "provider": "duckduckgo",
            "query": query,
            "count": len(results),
        }
    except Exception as e:
        return {"error": f"DuckDuckGo search failed: {e}", "provider": "duckduckgo", "query": query}


# =============================================================================
# URL Content Fetching
# =============================================================================

# Global rate limiter for URL fetching (prevents IP blocking)
_fetch_rate_limiter = None


def _get_fetch_rate_limiter() -> RateLimiter:
    """Get or create the fetch rate limiter."""
    global _fetch_rate_limiter
    if _fetch_rate_limiter is None:
        # Default: 1 request per 2 seconds to be conservative
        requests_per_second = float(os.getenv("FETCH_URL_RATE_LIMIT", "0.5"))
        _fetch_rate_limiter = RateLimiter(requests_per_second)
    return _fetch_rate_limiter


@tool
async def validate_url(url: str) -> dict:
    """
    Validate that a URL exists and is accessible via a lightweight HEAD request.

    Use this tool BEFORE any expensive operations like web scraping, dry_run,
    or ingestion. This is a cheap check (~100-500ms) vs fetching full content.

    CRITICAL: This tool is part of our zero-tolerance hallucination policy.
    Agents MUST validate any URL before using it, regardless of source:
    - URLs from web search results
    - URLs from LinkBase
    - URLs mentioned by users
    - URLs discovered via link-following

    Args:
        url: Full URL to validate (must start with http:// or https://)

    Returns:
        Dictionary with:
        - valid: Boolean - True if URL returns 2xx or 3xx status
        - url: The URL that was checked
        - status_code: HTTP status code (e.g., 200, 404, 500)
        - status_text: Human-readable status (e.g., "OK", "Not Found")
        - content_type: MIME type from Content-Type header (e.g., "text/html")
        - redirected_to: Final URL if redirected (only present if redirected)
        - error: (Only present if request failed) Error message
    """
    logger.info(f"Validating URL: {url}")

    # Validate URL format
    if not url.startswith(("http://", "https://")):
        return {
            "valid": False,
            "url": url,
            "error": "Invalid URL format. Must start with http:// or https://",
        }

    # No rate limiting for HEAD requests - they're lightweight
    try:
        timeout = float(os.getenv("VALIDATE_URL_TIMEOUT", "10.0"))
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; URLValidator/1.0)"
            }
        ) as client:
            response = await client.head(url)

            # Map common status codes to text
            status_texts = {
                200: "OK",
                201: "Created",
                204: "No Content",
                301: "Moved Permanently",
                302: "Found (Redirect)",
                304: "Not Modified",
                400: "Bad Request",
                401: "Unauthorized",
                403: "Forbidden",
                404: "Not Found",
                405: "Method Not Allowed",
                500: "Internal Server Error",
                502: "Bad Gateway",
                503: "Service Unavailable",
            }
            status_text = status_texts.get(response.status_code, f"HTTP {response.status_code}")

            # 2xx and 3xx are valid, 4xx and 5xx are not
            is_valid = 200 <= response.status_code < 400

            # Extract content-type header if available
            content_type = response.headers.get("content-type", "")
            # Clean up content-type (e.g., "text/html; charset=utf-8" -> "text/html")
            if ";" in content_type:
                content_type = content_type.split(";")[0].strip()

            result = {
                "valid": is_valid,
                "url": url,
                "status_code": response.status_code,
                "status_text": status_text,
                "content_type": content_type,
            }

            # Track if we were redirected
            if str(response.url) != url:
                result["redirected_to"] = str(response.url)

            logger.info(f"URL validation result: {url} -> {response.status_code} ({status_text})")
            return result

    except httpx.TimeoutException:
        logger.error(f"Timeout validating {url}")
        return {
            "valid": False,
            "url": url,
            "error": f"Timeout after {timeout}s. Server did not respond.",
        }

    except httpx.RequestError as e:
        logger.error(f"Request error validating {url}: {e}")
        return {
            "valid": False,
            "url": url,
            "error": f"Request failed: {str(e)}",
        }

    except Exception as e:
        logger.error(f"Unexpected error validating {url}: {e}")
        return {
            "valid": False,
            "url": url,
            "error": f"Unexpected error: {str(e)}",
        }


@tool
async def fetch_url(url: str, max_length: int = 8000) -> dict:
    """
    Fetch and extract the main text content from a webpage.

    Use this tool AFTER web_search to get full content from promising URLs.
    Search results only provide snippets - use this to read the actual page.

    IMPORTANT: This tool has rate limiting to prevent IP blocking. Don't call
    it on every search result - be selective about which pages to fetch.

    Best practices:
    - Use AFTER web_search identifies relevant URLs
    - Fetch 1-3 most promising results, not all of them
    - Great for documentation, articles, guides, tutorials
    - Automatically extracts main content (removes ads, navigation, etc.)

    Args:
        url: Full URL to fetch (must start with http:// or https://)
        max_length: Maximum content length to return (default: 8000 chars)

    Returns:
        Dictionary with:
        - content: Extracted text content from the page
        - url: The URL that was fetched
        - length: Character count of extracted content
        - truncated: Whether content was truncated
        - error: (Only present if fetch failed) Error message
    """
    logger.info(f"Fetching URL: {url}")

    # Validate URL format
    if not url.startswith(("http://", "https://")):
        return {
            "error": f"Invalid URL format. Must start with http:// or https://",
            "url": url,
        }

    # Apply rate limiting
    rate_limiter = _get_fetch_rate_limiter()
    await rate_limiter.wait()

    try:
        # Fetch with timeout and redirects
        timeout = float(os.getenv("FETCH_URL_TIMEOUT", "15.0"))
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; LinkScout/1.0; +https://github.com/example/linkscout)"
            }
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

        logger.info(f"Fetched {url}: {response.status_code}, {len(response.text)} bytes")

        # Extract main content using trafilatura
        content = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )

        if not content:
            return {
                "error": "Could not extract readable content. Page may be dynamic, require JavaScript, or be protected.",
                "url": url,
            }

        # Track if we truncated
        truncated = len(content) > max_length
        if truncated:
            content = content[:max_length] + "\n\n... [content truncated]"
            logger.info(f"Truncated content from {len(content)} to {max_length} chars")

        return {
            "content": content,
            "url": url,
            "length": len(content),
            "truncated": truncated,
        }

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
        return {
            "error": f"HTTP {e.response.status_code} error. Page may not exist or require authentication.",
            "url": url,
        }

    except httpx.TimeoutException:
        logger.error(f"Timeout fetching {url}")
        return {
            "error": f"Timeout after {timeout}s. Page took too long to respond.",
            "url": url,
        }

    except httpx.RequestError as e:
        logger.error(f"Request error fetching {url}: {e}")
        return {
            "error": f"Request failed: {str(e)}",
            "url": url,
        }

    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "url": url,
        }
