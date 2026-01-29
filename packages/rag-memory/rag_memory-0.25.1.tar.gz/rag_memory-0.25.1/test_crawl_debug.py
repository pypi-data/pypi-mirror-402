#!/usr/bin/env python3
"""Debug script to test what Crawl4AI is actually returning."""
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def test():
    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until='networkidle'
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
        print(f'Title: {result.metadata.get("title", "NO TITLE")}')
        print(f'\nContent preview (first 1000 chars):')
        print(result.markdown.raw_markdown[:1000])
        print(f'\n\nHTML title tag:')
        import re
        title_match = re.search(r'<title>([^<]+)</title>', result.html or '')
        if title_match:
            print(title_match.group(1))

asyncio.run(test())
