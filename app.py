import chainlit as cl
from tools import web_search_tool, scrape_source_tool


@cl.on_chat_start
async def setup_command_center():
    """
    Sends the welcome dashboard and the interactive Toolkit section.
    """
    # 1. Define the Toolkit actions (clickable buttons)
    toolkit_actions = [
        cl.Action(
            name="research_agent",
            payload={"value": "activate"},  # payload dict is required
            label="🔬 Research Agent",
            tooltip="Trigger the multi-agent search & validation engine.",
            icon="search"
        ),
        cl.Action(
            name="sheet_ops",
            payload={"value": "activate"},  # payload dict is required
            label="📊 SheetOps Toolkit",
            tooltip="Run structured spreadsheet updates.",
            icon="table"
        )
    ]

    # 2. Present the main dashboard to the user
    await cl.Message(
        content=(
            "### ⚡ Titan Operations Command Center\n"
            "Welcome. Titan is online and ready for execution. "
            "Select an operation from your workspace **Toolkit** below to begin:"
        ),
        actions=toolkit_actions
    ).send()


# 3. Intercept when the user clicks "Research Agent"
@cl.action_callback("research_agent")
async def on_research_agent_click(action: cl.Action):
    """
    Triggers when 'Research Agent' is clicked. Displays a prompt (popup)
    asking the user for their research target.
    """
    # Optional: Remove the toolkit button from this message once active
    await action.remove()

    # Trigger a clean prompt (equivalent to an interactive popup modal)
    user_prompt = await cl.AskUserMessage(
        content="🔬 **Titan Research Agent Initiated**\n\nWhat query, technology, or market topic should I analyze?",
        timeout=300  # Wait up to 5 minutes
    ).send()

    if user_prompt:
        query = user_prompt['output']

        # Start a parent pipeline step in the UI
        async with cl.Step(name="Titan Deep Intelligence Pipeline") as pipeline:
            pipeline.input = query

            # Step A: Perform search
            found_sources = await web_search_tool(query, max_results=3)

            if not found_sources:
                pipeline.output = "No search parameters resolved."
                await cl.Message(content="❌ Titan was unable to locate search directories for that topic.").send()
                return

            # Step B: Concurrent Crawling with Crawl4AI
            # Crawl each page and collect the raw data
            tasks = [
                scrape_source_tool(source['url'], source['title'])
                for source in found_sources
            ]
            scraped_contents = await asyncio.gather(*tasks)

            # Filter out failed scrapes
            valid_scrapes = [content for content in scraped_contents if content]

            # Step C: Log final data compilation status
            pipeline.output = f"Gathered {len(valid_scrapes)} deep source contexts. Ready for agent evaluation."

            # Send status update message
            await cl.Message(
                content=(
                    f"✅ **Core Web Retrieval Complete**\n"
                    f"Gathered content from {len(valid_scrapes)} locations. "
                    f"Check the sidebar panels to view the raw material.\n\n"
                    f"*Next step: Handing off to Titan's internal agent group (Analyst & Judge)...*"
                )
            ).send()


@cl.on_message
async def fallback_on_message(message: cl.Message):
    """Fallback handler for standard chat messages outside the toolkit."""
    await cl.Message(
        content="Please select an operation from the **Toolkit** above to start a structured process.").send()