from dataclasses import dataclass
import asyncio
import uuid
from typing import List
from agents import Agent, Runner, trace, function_tool, handoff

# IDEA HERE IS TO show streamed results
# similar example to 6_results.py but streamed

@dataclass
class UserContext:
    name: str
    language_preference: str

# Create some tools
@function_tool
async def get_weather(city: str) -> str:
    """Get the current weather for a city"""
    return f"The weather in {city} is sunny and 25°C"

@function_tool
async def translate_text(text: str, target_language: str) -> str:
    """Translate text to the target language"""
    if target_language.lower() == "spanish":
        return f"Translated to Spanish: Hola, {text}"
    elif target_language.lower() == "french":
        return f"Translated to French: Bonjour, {text}"
    else:
        return f"Translation to {target_language} not supported"

# Create specialized agents
spanish_agent = Agent[UserContext](
    name="Spanish Agent",
    instructions="You are a Spanish-speaking assistant. Always respond in Spanish.",
    tools=[get_weather, translate_text],
    model="gpt-4o-mini",
)

french_agent = Agent[UserContext](
    name="French Agent",
    instructions="You are a French-speaking assistant. Always respond in French.",
    tools=[get_weather, translate_text],
    model="gpt-4o-mini",
)

# Create a main triage agent with handoffs
triage_agent = Agent[UserContext](
    name="Triage Agent",
    instructions="""You are a helpful assistant that routes requests to the appropriate specialized agent.
    If the user wants Spanish, hand off to the Spanish Agent.
    If the user wants French, hand off to the French Agent.
    Otherwise, handle the request yourself.""",
    tools=[get_weather],
    handoffs=[spanish_agent, french_agent],
    model="gpt-4o-mini",
)

# Function to handle and display streaming events
async def process_stream_events(streaming_result, run_number):
    print(f"\n===== STREAMING RUN {run_number} EVENTS =====")
    
    token_output = ""
    
    async for event in streaming_result.stream_events():
        # Raw response events (token by token generation)
        if event.type == "raw_response_event":
            if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'content') and event.data.delta.content:
                token = event.data.delta.content
                token_output += token
                print(token, end="", flush=True)
        
        # Run item events (when an item is fully generated)
        elif event.type == "run_item_stream_event":
            print("\n\n[Event] New item generated:", event.item.type)
            
            if event.item.type == "tool_call_item":
                print(f"[Event] Tool called: {event.item.raw_item.name}")
                print(f"[Event] Arguments: {event.item.raw_item.arguments}")
                
            elif event.item.type == "tool_call_output_item":
                print(f"[Event] Tool output: {event.item.output}")
                
            elif event.item.type == "handoff_call_item":
                print(f"[Event] Handoff called: {event.item.raw_item.name}")
                
            elif event.item.type == "handoff_output_item":
                print(f"[Event] Handoff from: {event.item.source_agent.name}")
                print(f"[Event] Handoff to: {event.item.target_agent.name}")
                
        # Agent update events (when the agent changes, e.g., after handoff)
        elif event.type == "agent_updated_stream_event":
            print(f"\n[Event] Agent updated: {event.new_agent.name}")
    
    print("\n\nFinal response:", streaming_result.final_output)

async def main():
    # Create a user context
    user_context = UserContext(
        name="Alice",
        language_preference="multilingual"
    )
    
    # Generate a unique thread ID for this conversation
    thread_id = str(uuid.uuid4())
    
    with trace(workflow_name="Agent Streaming Demo", group_id=thread_id):
        # First run - Basic weather request with streaming
        print("\n----- STREAMING RUN 1: Basic weather request -----")
        result1 = Runner.run_streamed(
            triage_agent,
            "What's the weather in San Francisco?",
            context=user_context
        )
        await process_stream_events(result1, 1)
        
        # Store the last input for the next run
        last_input = result1.to_input_list()
        
        # Second run - Request in Spanish that should trigger handoff
        print("\n----- STREAMING RUN 2: Spanish request with handoff -----")
        result2 = Runner.run_streamed(
            triage_agent,
            last_input + [{"role": "user", "content": "I want to speak in Spanish. ¿Cómo está el clima en Madrid?"}],
            context=user_context
        )
        await process_stream_events(result2, 2)
        
        # Third run - Continue with the last agent directly
        print("\n----- STREAMING RUN 3: Using last agent directly -----")
        last_agent = result2.last_agent
        print(f"Continuing with last agent: {last_agent.name}")
        
        result3 = Runner.run_streamed(
            last_agent,  # Use the last agent instead of triage
            result2.to_input_list() + [{"role": "user", "content": "Gracias. ¿Puedes traducir 'hello' a español?"}],
            context=user_context
        )
        await process_stream_events(result3, 3)

if __name__ == "__main__":
    asyncio.run(main())
