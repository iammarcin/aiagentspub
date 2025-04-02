from pydantic import BaseModel
import asyncio
import uuid
from agents import Agent, Runner, trace, function_tool

# Define a structured output format
class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

# Create a tool that can retrieve previous events
@function_tool
async def get_previous_events(count: int) -> str:
    """Get information about previously scheduled events.
    
    Args:
        count: The number of previous events to retrieve
    """
    sample_events = [
        "Team meeting on 2025-05-15 with Alice, Bob, and Charlie",
        "Product launch on 2025-06-22 with Marketing team and executives",
    ]
    
    return "\n".join(sample_events[:count])

# Create our agent
agent = Agent(
    name="Calendar assistant",
    instructions="""You help users manage their calendar.
    Extract calendar events from text provided by the user.
    When extracting multiple events, separate them clearly.
    Use the get_previous_events tool if the user asks about previous events.""",
    model="gpt-4o-mini",
    output_type=CalendarEvent,
    tools=[get_previous_events]
)

async def main():
    # Generate a unique thread ID for this conversation
    thread_id = str(uuid.uuid4())
    
    with trace(workflow_name="Calendar Conversation", group_id=thread_id):
        # First turn - Extract a single event
        first_input = "Schedule a team meeting on May 15th with Alice, Bob, and Charlie"
        print(f"User: {first_input}")
        
        result = await Runner.run(agent, first_input)
        event = result.final_output
        print(f"Assistant extracted: {event}")
        
        # Second turn - Reference the previous event and add a new one
        # We use to_input_list() to include the previous conversation context
        second_query = "Also add a product launch on June 22nd with the marketing team and executives"
        print(f"Second query: {second_query}")
        second_input = result.to_input_list() + [
            {"role": "user", "content": second_query}
        ]
        
        # The agent now has context from the previous interaction
        result = await Runner.run(agent, second_input)
        event = result.final_output
        print(f"Assistant extracted: {event}")
        
        # Third turn - Ask about previous events
        third_query = "What events do I have scheduled?"
        print(f"Third query: {third_query}")
        third_input = result.to_input_list() + [
            {"role": "user", "content": third_query}
        ]
        
        # This will trigger the agent to use the get_previous_events tool
        # It can reference previous events from the conversation history
        result = await Runner.run(agent, third_input)
        print(f"Assistant response: {result.final_output}")

        # Fourth turn - Extract multiple events from a single message
        fourth_query = "Schedule a quarterly review on July 10th with management and department heads"
        print(f"Fourth query: {fourth_query}")
        fourth_input = result.to_input_list() + [
            {"role": "user", "content": fourth_query}
        ]
        
        result = await Runner.run(agent, fourth_input)
        event = result.final_output
        print(f"Assistant extracted: {event}")

if __name__ == "__main__":
    asyncio.run(main())