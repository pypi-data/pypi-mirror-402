#!/usr/bin/env python3
"""Test with EXACT web_crawler.py configuration."""
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def test():
    # EXACT browser config from web_crawler.py
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=[
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--single-process",
            "--no-zygote",
            "--disable-features=IsolateOrigins,site-per-process",
        ],
    )

    # EXACT crawler config from web_crawler.py (without markdown_generator for now)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=10,
        excluded_tags=[
            "nav", "footer", "header", "aside",
            "form", "iframe", "script", "style",
            "noscript", "meta", "link"
        ],
        remove_overlay_elements=True,
        simulate_user=True,
        magic=True,
        wait_until="networkidle",
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url='https://code.claude.com/docs/en/data-usage',
            config=crawler_config
        )

        print(f'URL: {result.url}')
        print(f'Redirected URL: {result.redirected_url}')
        print(f'Success: {result.success}')
        print(f'Status: {result.status_code}')
        print(f'Title from metadata: {result.metadata.get("title", "NO TITLE")}')

        # Check what markdown we get
        print(f'\nraw_markdown first 500 chars:')
        print(result.markdown.raw_markdown[:500])
        print(f'\nmarkdown_with_citations first 500 chars:')
        print(result.markdown.markdown_with_citations[:500])
        print(f'\nfit_markdown first 500 chars:')
        print(result.markdown.fit_markdown[:500] if result.markdown.fit_markdown else "EMPTY")

asyncio.run(test())
