import asyncio
import chainlit as cl
from tools import web_search_tool, scrape_source_tool
from agent import run_analyst_agent, run_judge_agent

@cl.on_chat_start
async def setup_command_center():
    """Sends the welcome dashboard and the interactive Toolkit section."""
    toolkit_actions = [
        cl.Action(
            name="research_agent", 
            payload={"value": "activate"},  
            label="🔬 Research Agent", 
            tooltip="Trigger the multi-agent search & validation engine.",
            icon="search"
        ),
        cl.Action(
            name="sheet_ops", 
            payload={"value": "activate"},  
            label="📊 SheetOps Toolkit", 
            tooltip="Run structured spreadsheet updates.",
            icon="table"
        )
    ]
    
    await cl.Message(
        content=(
            "### ⚡ Titan Operations Command Center\n"
            "Welcome. Titan is online and ready for execution. "
            "Select an operation from your workspace **Toolkit** below to begin:"
        ),
        actions=toolkit_actions
    ).send()

@cl.action_callback("research_agent")
async def on_research_agent_click(action: cl.Action):
    """Triggers the Iterative Multi-Agent Research Pipeline."""
    await action.remove()
    
    user_prompt = await cl.AskUserMessage(
        content="🔬 **Titan Research Agent Initiated**\n\nWhat query, technology, or market topic should I analyze?",
        timeout=300
    ).send()
    
    if not user_prompt:
        return
        
    query = user_prompt['output']
    accumulated_context = []
    
    # --- STAGE 1: INITIAL DATA GATHERING ---
    async with cl.Step(name="📡 Stage 1: Initial Intelligence Gathering") as step:
        step.input = query
        found_sources = await web_search_tool(query, max_results=3)
        if not found_sources:
            step.output = "Failed to resolve search parameters."
            await cl.Message(content="❌ Titan was unable to locate initial search directories.").send()
            return
            
        tasks = [scrape_source_tool(source['url'], source['title']) for source in found_sources]
        scraped_contents = await asyncio.gather(*tasks)
        valid_scrapes = [c for c in scraped_contents if c]
        accumulated_context.extend(valid_scrapes)
        step.output = f"Successfully gathered {len(valid_scrapes)} core directories."

    # --- STAGE 2: THE ITERATIVE AGENT LOOP ---
    draft_report = ""
    iteration = 1
    max_iterations = 2 # Prevent infinite loops
    
    while iteration <= max_iterations:
        # Step 2A: Analyst synthesizes report
        async with cl.Step(name=f"🤖 Analyst Agent (Drafting Revision #{iteration})") as step:
            step.input = query
            draft_report = await run_analyst_agent(
                query=query, 
                raw_context="\n\n".join(accumulated_context),
                revision_history=None if iteration == 1 else feedback_data
            )
            step.output = f"Generated a {len(draft_report.split())}-word technical report draft."
            
        # Step 2B: Judge evaluates report
        async with cl.Step(name=f"⚖️ Judge Agent (Evaluating Revision #{iteration})") as step:
            step.input = draft_report[:500] + "..." # Don't clutter logs
            evaluation = await run_judge_agent(
                query=query,
                draft_report=draft_report,
                raw_context="\n\n".join(accumulated_context)
            )
            
            evaluation_summary = (
                f"**Quality Grade:** {evaluation.grade}/10.0\n"
                f"**Approved:** {evaluation.approved}\n"
                f"**Criticism:** {evaluation.criticism}\n"
                f"**Identified Gaps:** {', '.join(evaluation.gaps_identified) if evaluation.gaps_identified else 'None'}"
            )
            step.output = evaluation_summary

        # Check if Judge approves or if we reached maximum iteration threshold
        if evaluation.approved or iteration == max_iterations:
            break
            
        # --- STAGE 2C: AUTONOMOUS GAP EXPANSION (Self-Correction) ---
        iteration += 1
        gap_query = evaluation.gaps_identified[0] if evaluation.gaps_identified else query
        
        async with cl.Step(name=f"🔄 Autonomous Self-Correction (Searching Gap: '{gap_query}')") as step:
            step.input = gap_query
            gap_sources = await web_search_tool(gap_query, max_results=2)
            if gap_sources:
                tasks = [scrape_source_tool(s['url'], s['title']) for s in gap_sources]
                gap_contents = await asyncio.gather(*tasks)
                valid_gap_scrapes = [c for c in gap_contents if c]
                accumulated_context.extend(valid_gap_scrapes)
                step.output = f"Scraped {len(valid_gap_scrapes)} additional sources to address gaps."
            else:
                step.output = "No search parameters resolved for gap query."
                
            # Compile feedback context for the Analyst's next iteration
            feedback_data = (
                f"### Judge Evaluation (Revision {iteration - 1}):\n"
                f"Grade: {evaluation.grade}\n"
                f"Criticism: {evaluation.criticism}\n\n"
                f"### Additional Researched Data on '{gap_query}':\n"
                f"{chr(10).join(valid_gap_scrapes) if gap_sources else 'No extra content found.'}"
            )

    # --- STAGE 3: OUTPUT FINAL COMPREHENSIVE REPORT ---
    await cl.Message(
        content=(
            f"## 🏆 Final Titan Technical Analysis\n\n"
            f"**Validation Grade:** `{evaluation.grade}/10.0` (Reviewed by Quality Judge)\n"
            f"**Iterations Executed:** `{iteration}`\n\n"
            f"---\n\n"
            f"{draft_report}"
        )
    ).send()

@cl.on_message
async def fallback_on_message(message: cl.Message):
    await cl.Message(content="Please select an operation from the **Toolkit** above to start a structured process.").send()