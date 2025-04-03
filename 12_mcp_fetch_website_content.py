import asyncio
import shutil
import json

from agents import Agent, Runner, trace
from agents.mcp import MCPServer, MCPServerStdio

# IDEA here is to show fetch content tool in action
# important differentatior - using raw mode - to get specific part of the page

async def run(mcp_server: MCPServer):
    # Simple variable to control raw parameter - change this before running
    USE_RAW = False
    
    # Create instructions based on raw setting
    raw_instruction = """When using the fetch tool, always use the 'raw' parameter set to true.""" if USE_RAW else ""
    
    agent = Agent(
        name="Assistant",
        instructions=f"""Gets URL from the user and fetches the content of the URL.
{raw_instruction}""",
        model="gpt-4o-mini",
        mcp_servers=[mcp_server],
    )

    #message = "Can you summarize it for me: https://www.cnet.com/news-live/switch-2-nintendo-direct-live-updates/ ?"
    message = "Can you extract main profile photo of fighter from this URL: https://www.ufc.com/athlete/alexander-volkanovski?"
    print("\n" + "-" * 40)
    print(f"Running: {message}")
    print(f"Using raw mode: {USE_RAW}")
    
    result = await Runner.run(starting_agent=agent, input=message)
    
    # Display fetch results from tool calls
    print("\n" + "-" * 40)
    print("Fetch Results:")
    
    # Iterate through items and find tool calls and their responses
    for i, item in enumerate(result.new_items):
        if item.type == "tool_call_item":
            print("\n" + "-" * 20)
            print(f"Tool Call #{i}:")
            print(f"Type: {item.raw_item.type}")
            # Safely print whatever attributes are available
            if hasattr(item, 'raw_item') and hasattr(item.raw_item, 'function'):
                print(f"Function: {item.raw_item.function.name}")
                if hasattr(item.raw_item.function, 'arguments'):
                    print(f"Arguments: {item.raw_item.function.arguments}")
        
        if item.type == "tool_call_output_item":
            print("\n" + "-" * 20)
            print(f"Tool Output #{i}:")
            # Truncate output if too long
            output = str(item.output)
            if len(output) > 500:
                output = output[:500] + "... [truncated]"
            print(f"Output: {output}")
    
    print("\n" + "-" * 40)
    print("Final Summary:")
    print(result.final_output)


async def main():
    async with MCPServerStdio(
        cache_tools_list=True,  # Cache the tools list, for demonstration
        params={"command": "uvx", "args": ["mcp-server-fetch"]},
    ) as server:
        with trace(workflow_name="MCP Fetch server"):
            await run(server)


if __name__ == "__main__":
    if not shutil.which("uvx"):
        raise RuntimeError("uvx is not installed. Please install it with `pip install uvx`.")

    asyncio.run(main()) 