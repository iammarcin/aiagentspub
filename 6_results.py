from dataclasses import dataclass
import asyncio
import uuid
from typing import List
from agents import Agent, Runner, trace, function_tool, handoff


# IDEA HERE IS TO show how results work

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

# Function to print details about the run result
def print_run_result(result, run_number):
    print(f"\n===== RUN {run_number} RESULTS =====")
    
    # Print the final output
    print("\nFINAL OUTPUT:")
    print(result.final_output)
    
    # Print information about the last agent
    print("\nLAST AGENT:")
    print(f"Name: {result.last_agent.name}")
    print(f"Model: {result.last_agent.model}")
    
    # Print all the new items generated during this run
    print("\nNEW ITEMS:")
    for i, item in enumerate(result.new_items):
        print(f"\nItem {i+1} ({item.type}):")
        
        if item.type == "message_output_item":
            print(f"  Message: {item.raw_item.content}")
            
        elif item.type == "tool_call_item":
            print(f"  Tool Called: {item.raw_item.name}")
            print(f"  Arguments: {item.raw_item.arguments}")
            
        elif item.type == "tool_call_output_item":
            print(f"  Tool Output: {item.output}")
            
        elif item.type == "handoff_call_item":
            print(f"  Handoff Called: {item.raw_item.name}")
            
        elif item.type == "handoff_output_item":
            print(f"  Handoff From: {item.source_agent.name}")
            print(f"  Handoff To: {item.target_agent.name}")
            
        elif item.type == "reasoning_item":
            print(f"  Reasoning: {item.raw_item.content}")

async def main():
    # Create a user context
    user_context = UserContext(
        name="Alice",
        language_preference="multilingual"
    )
    
    # Generate a unique thread ID for this conversation
    thread_id = str(uuid.uuid4())
    
    with trace(workflow_name="Agent Results Demo", group_id=thread_id):
        # First run - Basic weather request
        print("\n----- RUN 1: Basic weather request -----")
        result1 = await Runner.run(
            triage_agent,
            "What's the weather in San Francisco?",
            context=user_context
        )
        print_run_result(result1, 1)
        
        # Store the last input for the next run
        last_input = result1.to_input_list()
        
        # Second run - Request in Spanish that should trigger handoff
        print("\n----- RUN 2: Spanish request with handoff -----")
        result2 = await Runner.run(
            triage_agent,
            last_input + [{"role": "user", "content": "I want to speak in Spanish. ¿Cómo está el clima en Madrid?"}],
            context=user_context
        )
        print_run_result(result2, 2)
        
        # Third run - Continue with the last agent directly
        print("\n----- RUN 3: Using last agent directly -----")
        last_agent = result2.last_agent
        print(f"Continuing with last agent: {last_agent.name}")
        
        result3 = await Runner.run(
            last_agent,  # Use the last agent instead of triage
            result2.to_input_list() + [{"role": "user", "content": "Gracias. ¿Puedes traducir 'hello' a español?"}],
            context=user_context
        )
        print_run_result(result3, 3)

if __name__ == "__main__":
    asyncio.run(main())
