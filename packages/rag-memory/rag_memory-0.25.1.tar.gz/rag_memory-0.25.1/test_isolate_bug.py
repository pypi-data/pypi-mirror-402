#!/usr/bin/env python3
"""Isolate which config option causes the bug."""
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def test_config(name, **kwargs):
    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        **kwargs
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url='https://code.claude.com/docs/en/data-usage',
            config=crawler_config
        )

        title = result.metadata.get("title", "NO TITLE")
        print(f'{name}: {title}')
        return "Data usage" in title

print("Testing which config option causes the bug...\n")

async def run_tests():
    # Baseline
    await test_config("1. Baseline (no options)")

    # Test each option individually
    await test_config("2. wait_until=networkidle", wait_until="networkidle")
    await test_config("3. simulate_user=True", simulate_user=True)
    await test_config("4. magic=True", magic=True)

    # Test combinations
    await test_config("5. wait_until + simulate_user", wait_until="networkidle", simulate_user=True)
    await test_config("6. wait_until + magic", wait_until="networkidle", magic=True)
    await test_config("7. simulate_user + magic", simulate_user=True, magic=True)
    await test_config("8. ALL THREE", wait_until="networkidle", simulate_user=True, magic=True)

asyncio.run(run_tests())
