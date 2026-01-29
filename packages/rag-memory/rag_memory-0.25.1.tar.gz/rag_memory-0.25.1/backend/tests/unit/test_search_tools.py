"""
Unit tests for search_tools.py.

Tests RateLimiter, URL validation, and search providers.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_init_sets_min_interval(self):
        """RateLimiter calculates correct minimum interval."""
        from app.tools.search_tools import RateLimiter

        limiter = RateLimiter(requests_per_second=2.0)
        assert limiter.min_interval == 0.5

    def test_init_one_per_second(self):
        """RateLimiter with 1 req/sec has 1 second interval."""
        from app.tools.search_tools import RateLimiter

        limiter = RateLimiter(requests_per_second=1.0)
        assert limiter.min_interval == 1.0

    @pytest.mark.asyncio
    async def test_wait_no_delay_first_call(self):
        """First call to wait() should not delay significantly."""
        from app.tools.search_tools import RateLimiter

        limiter = RateLimiter(requests_per_second=10.0)

        start = time.time()
        await limiter.wait()
        elapsed = time.time() - start

        assert elapsed < 0.2  # Should be nearly instant

    @pytest.mark.asyncio
    async def test_wait_enforces_rate_limit(self):
        """Subsequent calls to wait() should enforce rate limit."""
        from app.tools.search_tools import RateLimiter

        limiter = RateLimiter(requests_per_second=20.0)  # 50ms interval

        await limiter.wait()
        start = time.time()
        await limiter.wait()
        elapsed = time.time() - start

        # Should wait at least most of the interval
        assert elapsed >= 0.03  # Allow some tolerance


class TestValidateUrl:
    """Tests for validate_url function."""

    @pytest.mark.asyncio
    async def test_valid_url_returns_true(self):
        """Valid URL with successful HEAD request returns valid=True."""
        from app.tools.search_tools import validate_url

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client_cls.return_value.__aexit__.return_value = None

            result = await validate_url.ainvoke({"url": "https://example.com"})

        assert result["valid"] is True
        assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_invalid_url_format(self):
        """URL without http/https returns error."""
        from app.tools.search_tools import validate_url

        result = await validate_url.ainvoke({"url": "not-a-url"})

        assert result["valid"] is False
        assert "error" in result
        assert "Invalid URL format" in result["error"]

    @pytest.mark.asyncio
    async def test_not_found_returns_false(self):
        """URL that returns 404 returns valid=False."""
        from app.tools.search_tools import validate_url

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com/nonexistent"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client_cls.return_value.__aexit__.return_value = None

            result = await validate_url.ainvoke({"url": "https://example.com/nonexistent"})

        assert result["valid"] is False
        assert result["status_code"] == 404

    @pytest.mark.asyncio
    async def test_timeout_returns_error(self):
        """Timeout returns valid=False with error message."""
        from app.tools.search_tools import validate_url
        import httpx

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client_cls.return_value.__aexit__.return_value = None

            result = await validate_url.ainvoke({"url": "https://slow.test"})

        assert result["valid"] is False
        assert "error" in result
        assert "Timeout" in result["error"]


class TestWebSearchImpl:
    """Tests for internal _web_search_impl function."""

    @pytest.mark.asyncio
    async def test_google_success(self):
        """Google search returns results with provider=google."""
        from app.tools.search_tools import _web_search_impl, SearchResult
        import app.tools.search_tools as module

        # Reset global providers
        module._google_provider = None
        module._duckduckgo_provider = None

        mock_provider = MagicMock()
        mock_provider.search = AsyncMock(return_value=[
            SearchResult(title="Result 1", url="https://example.com", snippet="Test")
        ])

        with patch.object(module, "GoogleSearchProvider", return_value=mock_provider):
            results, provider, error = await _web_search_impl("test query", 5)

        assert provider == "google"
        assert len(results) == 1
        assert error is None

    @pytest.mark.asyncio
    async def test_fallback_to_duckduckgo(self):
        """Falls back to DuckDuckGo when Google fails."""
        from app.tools.search_tools import _web_search_impl, SearchResult
        import app.tools.search_tools as module

        # Reset global providers
        module._google_provider = None
        module._duckduckgo_provider = None

        mock_ddg = MagicMock()
        mock_ddg.search = AsyncMock(return_value=[
            SearchResult(title="DDG Result", url="https://ddg.com", snippet="Test")
        ])

        with patch.object(module, "GoogleSearchProvider", side_effect=ValueError("No creds")):
            with patch.object(module, "DuckDuckGoSearchProvider", return_value=mock_ddg):
                results, provider, error = await _web_search_impl("test query", 5)

        assert provider == "duckduckgo"
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_both_fail_returns_empty(self):
        """Returns empty results when both providers fail."""
        from app.tools.search_tools import _web_search_impl
        import app.tools.search_tools as module

        # Reset global providers
        module._google_provider = None
        module._duckduckgo_provider = None

        with patch.object(module, "GoogleSearchProvider", side_effect=ValueError("No creds")):
            with patch.object(module, "DuckDuckGoSearchProvider", side_effect=Exception("DDG error")):
                results, provider, error = await _web_search_impl("test query", 5)

        assert provider == "none"
        assert len(results) == 0
        assert error is not None


class TestGoogleSearchProvider:
    """Tests for GoogleSearchProvider class."""

    def test_init_raises_without_credentials(self):
        """GoogleSearchProvider raises ValueError without credentials."""
        from app.tools.search_tools import GoogleSearchProvider

        with patch.dict("os.environ", {"GOOGLE_API_KEY": "", "GOOGLE_CSE_ID": ""}, clear=False):
            with pytest.raises(ValueError, match="requires GOOGLE_API_KEY"):
                GoogleSearchProvider()

    def test_init_succeeds_with_credentials(self):
        """GoogleSearchProvider initializes with valid credentials."""
        from app.tools.search_tools import GoogleSearchProvider

        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test_key", "GOOGLE_CSE_ID": "test_cse"}):
            with patch("app.tools.search_tools.GoogleSearchAPIWrapper"):
                provider = GoogleSearchProvider()
                assert provider.rate_limiter is not None


class TestDuckDuckGoSearchProvider:
    """Tests for DuckDuckGoSearchProvider class."""

    def test_init_succeeds(self):
        """DuckDuckGoSearchProvider initializes without credentials."""
        from app.tools.search_tools import DuckDuckGoSearchProvider

        with patch("app.tools.search_tools.DuckDuckGoSearchAPIWrapper"):
            provider = DuckDuckGoSearchProvider()
            assert provider.rate_limiter is not None

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """DuckDuckGo search returns formatted results."""
        from app.tools.search_tools import DuckDuckGoSearchProvider

        mock_wrapper = MagicMock()
        mock_wrapper.results.return_value = [
            {"title": "Test", "link": "https://test.com", "snippet": "Test snippet"}
        ]

        with patch("app.tools.search_tools.DuckDuckGoSearchAPIWrapper", return_value=mock_wrapper):
            provider = DuckDuckGoSearchProvider()

            # Mock the async call
            with patch.object(provider.rate_limiter, "wait", new_callable=AsyncMock):
                with patch("asyncio.get_event_loop") as mock_loop:
                    mock_loop.return_value.run_in_executor = AsyncMock(
                        return_value=[{"title": "Test", "link": "https://test.com", "snippet": "Test"}]
                    )
                    with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait_for:
                        mock_wait_for.return_value = [{"title": "Test", "link": "https://test.com", "snippet": "Test"}]
                        results = await provider.search("test", 5)

        assert len(results) == 1
        assert results[0].title == "Test"
