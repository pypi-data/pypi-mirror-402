#!/usr/bin/env python3
"""Test after removing simulate_user and magic."""
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def test():
    browser_config = BrowserConfig(headless=True, verbose=False)

    # Config AFTER removing simulate_user and magic
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=10,
        excluded_tags=[
            "nav", "footer", "header", "aside",
            "form", "iframe", "script", "style",
            "noscript", "meta", "link"
        ],
        remove_overlay_elements=True,
        wait_until="networkidle",  # Keep this - it was working on Dec 21st
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url='https://code.claude.com/docs/en/data-usage',
            config=crawler_config
        )

        title = result.metadata.get("title", "NO TITLE")
        print(f'Title: {title}')
        print(f'CORRECT PAGE: {"Data usage" in title}')
        print(f'\nFirst 500 chars of content:')
        print(result.markdown.markdown_with_citations[:500])

asyncio.run(test())
