import asyncio
import json
import os

from agents import Agent, Runner, trace
from agents.mcp import MCPServer, MCPServerStdio


async def run(mcp_server: MCPServer):

    # we have cached list of tools, but here we do it to debug
    try:
        print("Attempting to list tools from MCP server...")
        tools = await mcp_server.list_tools()
        print("\n" + "-" * 40)
        print("Available Google Maps Tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
    except Exception as e:
        print(f"Error listing tools: {e}")
        raise
    
    agent = Agent(
        name="Distance Calculator",
        instructions="""You are a helpful assistant that calculates distances between locations.
        
        When asked about distances between places, use the Google Maps tools to provide accurate information.
        Specifically, use the maps_distance_matrix tool to get distance and travel time information.
        
        Always report both distance and travel time in your final answer.
        """,
        model="gpt-4o-mini",
        mcp_servers=[mcp_server],
    )

    
    #message = "What is the distance between Barcelona and Lisbon? Can you also tell me how long it would take to drive between these cities?"

    #message = "What is the distance and time needed between Barcelona and Lisbon if i want to go the by bicycle?"

    #message = "What is the distance and time needed between Barcelona and Lisbon if i want to go the by plane?"
    message = "What is the distance and time needed between Barcelona and Lisbon? I would like to get the table for plane, car, bicycle and walking."
    print("\n" + "-" * 40)
    print(f"Running: {message}")
    
    result = await Runner.run(starting_agent=agent, input=message)
    
    # Display fetch results from tool calls
    print("\n" + "-" * 40)
    print("Tool Calls and Results:")
    
    # Iterate through items and find tool calls and their responses
    for i, item in enumerate(result.new_items):
        if item.type == "tool_call_item":
            print("\n" + "-" * 20)
            print(f"Tool Call #{i}:")
            print(f"Type: {item.raw_item.type}")
            if hasattr(item, 'params') and item.params:
                print(f"Params: {json.dumps(item.params, indent=2)}")
        
        if item.type == "tool_call_output_item":
            print("\n" + "-" * 20)
            print(f"Tool Output #{i+1}:")
            try:
                # Try to parse the output as JSON for better formatting
                output_json = json.loads(item.output)
                print(f"Output: {json.dumps(output_json, indent=2)}")
            except (json.JSONDecodeError, AttributeError):
                # If not JSON or no output attribute, print as is
                output = str(item.output)
                if len(output) > 500:
                    output = output[:1000] + "... [truncated]"
                print(f"Output: {output}")
    
    print("\n" + "-" * 40)
    print("Final Answer:")
    print(result.final_output)


async def main():
    # Ensure the API key is set
    if not os.environ.get("GOOGLE_MAPS_API_KEY"):
        raise RuntimeError("GOOGLE_MAPS_API_KEY environment variable is not set.")

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")

    try:
        async with MCPServerStdio(
            cache_tools_list=True,
            params={
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-google-maps"],
                "env": {
                    "GOOGLE_MAPS_API_KEY": api_key
                }
            },
        ) as server:
            # Run the query with tracing enabled
            with trace(workflow_name="Google Maps Distance Calculator"):
                await run(server)
    except Exception as e:
        print(f"Error connecting to MCP server: {str(e)}")
        print("Detailed error information:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 