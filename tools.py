import asyncio
import urllib.parse
from bs4 import BeautifulSoup
import chainlit as cl
from playwright.async_api import async_playwright
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


def clean_ddg_url(raw_url: str) -> str:
    """
    DuckDuckGo HTML results use a redirect wrapper.
    This decodes and extracts the actual destination URL.
    """
    if "uddg=" in raw_url:
        parsed = urllib.parse.urlparse(raw_url)
        queries = urllib.parse.parse_qs(parsed.query)
        if "uddg" in queries:
            return queries["uddg"][0]
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    return raw_url


async def web_search_tool(query: str, max_results: int = 3) -> list[dict]:
    """
    Uses the container's Playwright engine to search DuckDuckGo safely,
    bypassing cloud IP blocking, and parses the static HTML SERP.
    """
    async with cl.Step(name="🔍 Searching Web Directories", type="tool") as step:
        step.input = query
        found = []
        try:
            # Leverage our native Playwright installation
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                # Emulate a standard Windows Chrome browser session
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                # Fetch keyless HTML DuckDuckGo search page
                encoded_query = urllib.parse.quote_plus(query)
                search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

                await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
                content = await page.content()
                await browser.close()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            result_elements = soup.select("#links .result")

            for elem in result_elements[:max_results]:
                # Locate the result anchor tag
                link_elem = elem.select_one(".result__title > a.result__a")
                if link_elem:
                    title = link_elem.get_text(strip=True)
                    raw_href = link_elem.get("href", "")
                    clean_url = clean_ddg_url(raw_href)
                    found.append({"url": clean_url, "title": title})

            # Feed success status back to Chainlit UI
            if found:
                urls_formatted = "\n".join([f"- [{r['title']}]({r['url']})" for r in found])
                step.output = f"Discovered target URLs:\n{urls_formatted}"
            else:
                step.output = "No matches found on the search page."

        except Exception as e:
            step.output = f"Playwright Search Error: {str(e)}"
            found = []

        return found


async def scrape_source_tool(url: str, source_title: str) -> str:
    """
    Crawls a single webpage using Crawl4AI and displays live progress in the UI.
    """
    domain = url.split("//")[-1].split("/")[0]

    async with cl.Step(name=f"🕷️ Crawling {domain}", type="tool") as step:
        step.input = url

        browser_cfg = BrowserConfig(headless=True, verbose=False)
        run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)
            if result.success:
                word_count = len(result.markdown.split())
                step.output = f"Successfully scraped {word_count} words of text context."

                # Register in the collapsible side-inspection panel
                raw_source_element = cl.Text(
                    name=f"Source: {source_title}",
                    content=result.markdown,
                    display="side",
                    language="markdown"
                )
                await raw_source_element.send()

                return result.markdown
            else:
                step.output = f"Failed to crawl. Status: {result.status_code}"
                return ""