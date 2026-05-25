import os
from pydantic import BaseModel, Field
from config import client, MODEL_NAME

# The Pydantic Schema that the Judge must complete
class ResearchEvaluation(BaseModel):
    grade: float = Field(
        description="A quality grade from 0.0 to 10.0 assessing the completeness, technical depth, and structure of the report."
    )
    approved: bool = Field(
        description="True if the grade is 8.0 or above and has no critical missing information. False if it has gaps that require more web research."
    )
    gaps_identified: list[str] = Field(
        description="Specific technical topics, missing data points, or unverified claims that must be searched to make the report complete. Empty list if approved."
    )
    criticism: str = Field(
        description="Constructive and critical feedback detailing how the Analyst Agent should expand the report."
    )

# 1. The Analyst Agent Prompt
ANALYST_SYSTEM_PROMPT = """
You are Titan's Lead Technical & Market Research Analyst. Your job is to take raw, crawled website markdown data on a specific topic and compile it into an extremely rigorous, structured, and deep research report.

Guidelines:
- Draft a comprehensive, professional report using markdown formatting.
- Include deep technical descriptions, clear headings, and bullet points.
- Implement structured comparison tables, code blocks, or mathematical formulas if relevant.
- Do not make up facts; rely strictly on the raw context provided.
- If some information is missing, state it clearly in a dedicated 'Omissions' section.
"""

# 2. The Judge Agent Prompt
JUDGE_SYSTEM_PROMPT = """
You are Titan's Quality Control Evaluator. Your job is to critically evaluate a synthesized draft research report against the user's original query and the raw context provided.

Be incredibly demanding. If the report contains vague summaries, lacks concrete metrics, or omits crucial information available in the context (or logically expected for the query), evaluate it as NOT approved, identify the exact gaps to be researched, and give critical feedback.
"""

async def run_analyst_agent(query: str, raw_context: str, revision_history: str = None) -> str:
    """
    Directs the Analyst Agent to generate (or revise) the technical report.
    """
    messages = [
        {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
        {"role": "user", "content": f"User Query: {query}\n\nRaw Context:\n{raw_context}"}
    ]
    
    if revision_history:
        messages.append({
            "role": "user", 
            "content": f"The previous draft was evaluated. Here is the feedback and additional context gathered:\n{revision_history}\n\nPlease revise, improve, and significantly expand the report based on this guidance."
        })
        
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages
    )
    return response.choices[0].message.content

async def run_judge_agent(query: str, draft_report: str, raw_context: str) -> ResearchEvaluation:
    """
    Directs the Judge Agent to evaluate the drafted report using Structured Outputs (Pydantic).
    """
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {
            "role": "user", 
            "content": f"Original Query: {query}\n\nRaw context:\n{raw_context}\n\nDraft Report:\n{draft_report}"
        }
    ]
    
    response = await client.beta.chat.completions.parse(
        model=MODEL_NAME,
        messages=messages,
        response_format=ResearchEvaluation
    )
    return response.choices[0].message.parsed