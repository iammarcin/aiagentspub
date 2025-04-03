from agents import Agent, FileSearchTool, Runner, WebSearchTool
import asyncio

# IDEA HERE IS TO show how to use tools
# we have file search tool (with some documentation) and web search tool

agent = Agent(
    name="Assistant",
    model="gpt-4o-mini",
    tools=[
        WebSearchTool(),
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["vs_67dfa15ad9008191a806e333f123cd20"],
        ),
    ],
)

# Function to print details about the run result - improved for hosted tools
def print_run_result(result):
    print("\n===== RUN RESULTS =====")
    
    # Print the final output
    print("\nFINAL OUTPUT:")
    print(result.final_output)
    
    # Print information about the last agent
    print("\nAGENT:")
    print(f"Name: {result.last_agent.name}")
    
    # Print all the new items generated during this run
    print("\nITEMS GENERATED:")
    for i, item in enumerate(result.new_items):
        print(f"\nItem {i+1} ({item.type}):")
        
        if item.type == "message_output_item":
            print(f"  Message: {item.raw_item.content}")
            
        elif item.type == "tool_call_item":
            # Handle different tool types
            if hasattr(item.raw_item, 'name'):
                # Function tool
                print(f"  Tool Called: {item.raw_item.name}")
                print(f"  Arguments: {item.raw_item.arguments}")
            elif hasattr(item.raw_item, 'type'):
                # Hosted tool like web search
                print(f"  Tool Called: {item.raw_item.type}")
                
                # Different tools have different parameter structures
                if item.raw_item.type == "web_search":
                    print(f"  Search Query: {item.raw_item.web_search.query}")
                elif item.raw_item.type == "retrieval":
                    print(f"  Retrieval Query: {item.raw_item.retrieval.query}")
                else:
                    print(f"  Tool Parameters: {item.raw_item}")
            else:
                # Fallback for unknown structure
                print(f"  Tool Details: {item.raw_item}")
            
        elif item.type == "tool_call_output_item":
            print(f"  Tool Output: {item.output}")
            
        elif item.type == "reasoning_item":
            print(f"  Reasoning: {item.raw_item.content}")

async def main():
    #print("===== RUNNING QUERY 1 =====")
    #result = await Runner.run(agent, "How do we create an HTML page with a button?")
    
    # Print detailed information about the run result
    #print_run_result(result)
    
    # Run another query to demonstrate different tool usage
    print("\n\n===== RUNNING QUERY 2 =====")
    result2 = await Runner.run(agent, "What's the latest in world of NBA?")
    print_run_result(result2)

if __name__ == "__main__":
    asyncio.run(main())