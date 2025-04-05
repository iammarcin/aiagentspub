import asyncio
import shutil
import time
from datetime import datetime
from typing import Dict, Any

from agents import Agent, Runner, trace
from agents.mcp import MCPServer, MCPServerStdio
from pydantic import BaseModel

# IDEA here is to show parallel execution in action
# important part is that we are using asyncio.gather to run tasks in parallel


# Define a simple output type for our agents
class WebsiteAnalysis(BaseModel):
    url: str
    summary: str
    analysis_time: str

async def run_agent(agent: Agent, message: str, ctx: Dict[str, Any] = None) -> WebsiteAnalysis:
    """Run a single agent and return its output with timing information"""
    start_time = time.time()
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] Starting agent: {agent.name}")
    
    # Run the agent
    result = await Runner.run(starting_agent=agent, input=message, context=ctx)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    print(f"[{timestamp}] Completed agent: {agent.name} in {execution_time:.2f} seconds")
    
    # Extract just the summary from the output, avoiding raw HTML
    if hasattr(result, 'final_output') and hasattr(result.final_output, 'model_dump'):
        output = result.final_output.model_dump()
        return WebsiteAnalysis(
            url=output.get('url', message),
            summary=output.get('summary', str(result.final_output)),
            analysis_time=f"{execution_time:.2f}s"
        )
    else:
        # Handle non-structured output
        return WebsiteAnalysis(
            url=message,
            summary=str(result.final_output),
            analysis_time=f"{execution_time:.2f}s"
        )

async def run(mcp_server: MCPServer):
    # Create specialized agents for different analysis tasks
    news_agent = Agent(
        name="News Analyzer",
        instructions="""You are a specialized agent that analyzes news websites.
        When given a URL, fetch its content and provide a brief summary of the news article.
        Focus on key facts, dates, and main points. 
        IMPORTANT: Do NOT include raw HTML in your summary.""",
        model="gpt-4o-mini",
        mcp_servers=[mcp_server],
        output_type=WebsiteAnalysis,
    )

    profile_agent = Agent(
        name="Profile Analyzer",
        instructions="""You are a specialized agent that analyzes profile pages.
        When given a URL, fetch its content and extract biographical information.
        Focus on the person's achievements, statistics, and career highlights.
        IMPORTANT: Do NOT include raw HTML in your summary.""",
        model="gpt-4o-mini",
        mcp_servers=[mcp_server],
        output_type=WebsiteAnalysis,
    )

    summarizer_agent = Agent(
        name="Results Summarizer",
        instructions="""You are a specialized agent that combines results from two analyses.
        Create a comprehensive summary that integrates insights from both analyses.
        Be concise and focus on the most important information.""",
        model="gpt-4o-mini"
    )

    # URLs to analyze
    url1 = "https://www.nba.com/player/1627759/jaylen-brown"
    url2 = "https://www.yardbarker.com/nba/articles/jaylen_browns_worrying_injury_admission_after_heat_snap_celtics_9_game_win_streak_not_gonna_feel_like_my_normal_self/s1_17149_41998117"
    
    print("\n" + "-" * 60)
    print(f"Starting parallel analysis of two websites...")
    print("-" * 60)
    
    # Run the two analysis agents in parallel using asyncio.gather
    start_time = time.time()
    profile_task = run_agent(profile_agent, url1)
    news_task = run_agent(news_agent, url2)
    
    # THIS IS THE KEY PART - using asyncio.gather to run tasks in parallel
    profile_result, news_result = await asyncio.gather(profile_task, news_task)
    
    parallel_execution_time = time.time() - start_time
    print(f"\n[INFO] Both analyses completed in {parallel_execution_time:.2f} seconds")
    
    # Display individual results
    print("\n" + "-" * 60)
    print(f"Profile Analysis Results ({profile_result.analysis_time}):")
    print("-" * 60)
    print(profile_result.summary)
    
    print("\n" + "-" * 60)
    print(f"News Analysis Results ({news_result.analysis_time}):")
    print("-" * 60)
    print(news_result.summary)
    
    # Now run the summarizer with both results as input
    print("\n" + "-" * 60)
    print("Running final summarizer...")
    summarizer_start = time.time()
    
    combined_input = f"""I have analyzed two websites:

1. Profile Analysis ({profile_result.url}):
{profile_result.summary}

2. News Analysis ({news_result.url}):
{news_result.summary}

Please provide a comprehensive summary combining these insights.
"""
    
    summarizer_result = await Runner.run(starting_agent=summarizer_agent, input=combined_input)
    summarizer_time = time.time() - summarizer_start
    
    # Display final summary
    print("\n" + "-" * 60)
    print(f"Final Summary (completed in {summarizer_time:.2f} seconds):")
    print("-" * 60)
    print(summarizer_result.final_output)
    
    # Show overall execution statistics
    total_time = time.time() - start_time
    sequential_time = float(profile_result.analysis_time[:-1]) + float(news_result.analysis_time[:-1]) + summarizer_time
    time_saved = sequential_time - total_time
    
    print("\n" + "-" * 60)
    print("Execution Statistics:")
    print("-" * 60)
    print(f"Profile Analysis Time: {profile_result.analysis_time}")
    print(f"News Analysis Time: {news_result.analysis_time}")
    print(f"Summarizer Time: {summarizer_time:.2f}s")
    print(f"Total Execution Time: {total_time:.2f}s")
    print(f"Estimated Sequential Time: {sequential_time:.2f}s")
    print(f"Time Saved with Parallel Execution: {time_saved:.2f}s ({(time_saved/sequential_time*100):.1f}%)")

async def main():
    async with MCPServerStdio(
        cache_tools_list=True,
        params={"command": "uvx", "args": ["mcp-server-fetch"]},
    ) as server:
        with trace(workflow_name="True Parallel Website Analysis"):
            await run(server)

if __name__ == "__main__":
    if not shutil.which("uvx"):
        raise RuntimeError("uvx is not installed. Please install it with `pip install uvx`.")

    asyncio.run(main())
