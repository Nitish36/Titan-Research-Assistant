import asyncio
import chainlit as cl
from duckduckgo_search import DDGS
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


async def web_search_tool(query: str, max_results: int = 3) -> list[dict]:
    """
    Performs a web search and communicates progress to the UI using a nested Step.
    """
    # Create a visual step in the Chainlit UI
    async with cl.Step(name="🔍 Searching Web Directories", type="tool") as step:
        step.input = query
        try:
            with DDGS() as ddg:
                results = ddg.text(query, max_results=max_results)
                found = []
                for r in results:
                    if 'href' in r:
                        found.append({"url": r['href'], "title": r.get('title', 'Source')})

                # Report back to the UI what was found
                if found:
                    urls_formatted = "\n".join([f"- [{r['title']}]({r['url']})" for r in found])
                    step.output = f"Discovered target URLs:\n{urls_formatted}"
                else:
                    step.output = "No matches discovered."
                return found
        except Exception as e:
            step.output = f"Search directory error: {str(e)}"
            return []


async def scrape_source_tool(url: str, source_title: str) -> str:
    """
    Crawls a single webpage using Crawl4AI, displays live progress in the UI,
    and returns clean Markdown.
    """
    domain = url.split("//")[-1].split("/")[0]

    # Create a dynamic sub-step for this specific crawling task
    async with cl.Step(name=f"🕷️ Crawling {domain}", type="tool") as step:
        step.input = url

        browser_cfg = BrowserConfig(headless=True, verbose=False)
        run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)
            if result.success:
                word_count = len(result.markdown.split())
                step.output = f"Successfully scraped {word_count} words of text context."

                # We attach the raw crawled markdown as a clickable Side Element!
                # This lets the user inspect what Titan read in a split-screen view.
                raw_source_element = cl.Text(
                    name=f"Source: {source_title}",
                    content=result.markdown,
                    display="side",  # Displays in the sidebar when clicked
                    language="markdown"
                )
                await raw_source_element.send()

                return result.markdown
            else:
                step.output = f"Failed to crawl. Status code: {result.status_code}"
                return ""