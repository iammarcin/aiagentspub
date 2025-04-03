from agents import Agent, Runner
import asyncio

# IDEA HERE IS TO show how to use agents as tools
# this is copy paste from openai documentation
# it's bit different approach than with just functions - but yeah it makes sense in some cases

spanish_agent = Agent(
    name="Spanish agent",
    model="gpt-4o-mini",
    instructions="You translate the user's message to Spanish",
)

french_agent = Agent(
    name="French agent",
    model="gpt-4o-mini",
    instructions="You translate the user's message to French",
)

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        "You are a translation agent. You use the tools given to you to translate."
        "If asked for multiple translations, you call the relevant tools."
    ),
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate the user's message to Spanish",
        ),
        french_agent.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate the user's message to French",
        ),
    ],
)

async def main():
    result = await Runner.run(orchestrator_agent, input="Say 'Hello, how are you?' in Spanish.")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())