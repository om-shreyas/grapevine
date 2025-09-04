from typing import List
from mcp.server.fastmcp import FastMCP
from quiz import generate_quiz_questions
from news import search_job_news as search_news
from job_search import search_jobs

mcp = FastMCP("career-agent-tools")

@mcp.tool()
async def fetch_quiz_questions(
    user_id: str,
    text: str,
    resume: str,
    role: str,
    past_qs: List[str],
) -> List[str]:
    """Return interview practice questions. Uses user_id + text for personalization."""
    return generate_quiz_questions(user_id=user_id, resume=resume, role=role, past_questions=past_qs)

@mcp.tool()
async def search_job_news(
    user_id: str,
    text: str,
    topic: str,
) -> str:
    """Return recent job/upskilling news for a topic."""
    return search_news(topic=topic, user_id=user_id)

@mcp.tool()
async def find_jobs(
    user_id: str,
    text: str,
    query: str = None,
    top_k: int = 5,
) -> List[dict]:
    """Search for job opportunities based on user resume or query."""
    return search_jobs(user_id=user_id, query=query, top_k=top_k)

if __name__ == "__main__":
    import asyncio
    from mcp.server import stdio

    async def run():
        async with stdio.stdio_server() as (read, write):
            await mcp.run(read, write)

    asyncio.run(run())