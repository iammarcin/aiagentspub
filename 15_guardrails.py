from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    input_guardrail,
)

# IDEA here is to show guardrails in action
# one important use case:
# if we use big expensive model - its worth to do guardrails with cheap model so big one is not even executed
# also important it is using tripwire to catch error (if it's not on topic) - so we can display proper error message

# Define output type for the guardrail
class TopicCheckOutput(BaseModel):
    is_nba_related: bool
    reasoning: str

# Create a guardrail agent that checks if the question is NBA-related
guardrail_agent = Agent(
    name="Topic Checker",
    instructions="""You are a topic checker. Your job is to determine if a question is related to NBA basketball.
    Consider topics like:
    - NBA teams, players, and games
    - NBA history and statistics
    - NBA rules and regulations
    - NBA championships and records
    
    If the question is not about NBA basketball, explain why it's off-topic.
    If it is about NBA basketball, explain why it's relevant.""",
    output_type=TopicCheckOutput,
    model="gpt-4o-mini",
)

# Define the guardrail function
@input_guardrail
async def nba_topic_guardrail(
    ctx: RunContextWrapper[None], 
    agent: Agent, 
    input: str
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_nba_related,
    )

# Create the main NBA agent
nba_agent = Agent(
    name="NBA Expert",
    instructions="""You are an NBA basketball expert. You provide detailed information about:
    - NBA teams, players, and games
    - NBA history and statistics
    - NBA rules and regulations
    - NBA championships and records
    
    Always provide accurate and up-to-date information about the NBA.""",
    input_guardrails=[nba_topic_guardrail],
    model="gpt-4o-mini",
)

async def main():
    # Example 1: NBA-related question (should work)
    try:
        result = await Runner.run(nba_agent, "Who won the 2023 NBA Finals?")
        print("NBA Question Result:", result.final_output)
    except InputGuardrailTripwireTriggered as e:
        print("Guardrail triggered for NBA question (unexpected):", e.guardrail_result.reasoning)

    # Example 2: Non-NBA question (should trigger guardrail)
    try:
        result = await Runner.run(nba_agent, "What's the weather like in Paris?")
        print("This should not be reached")
    except InputGuardrailTripwireTriggered as e:
        print("\nOff-topic Question Response:")
        print("I apologize, but I'm specifically designed to answer questions about NBA basketball.")
        print("Please feel free to ask any questions about NBA basketball instead!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



