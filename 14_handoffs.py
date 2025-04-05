from pydantic import BaseModel

from agents import Agent, handoff, RunContextWrapper, Runner
from agents.extensions import handoff_filters

import asyncio
# IDEA here is to show handoff in action
# important is that on_handoff event can be called !
# When a handoff occurs, it's as though the new agent takes over the conversation, and gets to see the entire previous conversation history.
# We can change it (for example removing all tool calls from the history), which are implemented for you in agents.extensions.handoff_filters
# ALSO! very important is prompt  / instructions
# agents.extensions.handoff_prompt.RECOMMENDED_PROMPT_PREFIX, or you can call agents.extensions.handoff_prompt.prompt_with_handoff_instructions to automatically add recommended data to your prompts.
# https://openai.github.io/openai-agents-python/ref/extensions/handoff_prompt/#agents.extensions.handoff_prompt.RECOMMENDED_PROMPT_PREFIX
# https://openai.github.io/openai-agents-python/ref/extensions/handoff_prompt/#agents.extensions.handoff_prompt.prompt_with_handoff_instructions

class EscalationData(BaseModel):
    reason: str

async def on_handoff(ctx: RunContextWrapper[None], input_data: EscalationData):
    print(f"Escalation agent called with reason: {input_data.reason}")

escalation_agent = Agent(
    name="Escalation agent",
    model="gpt-4o-mini",
    instructions="You are a helpful assistant that can help with escalation of issues. You will be given a reason for the escalation and you will need to help the user with the issue."
)

handoff_obj = handoff(
    agent=escalation_agent,
    on_handoff=on_handoff,
    input_type=EscalationData,
    input_filter=handoff_filters.remove_all_tools, 
)

# Main agent that can hand off to escalation
main_agent = Agent(
    name="Main agent",
    model="gpt-4o-mini",
    instructions="""You are a helpful assistant. If the user's request requires escalation, 
    use the transfer_to_escalation_agent tool and provide a reason for the escalation.
    Otherwise, try to help the user directly.""",
    handoffs=[handoff_obj]
)

async def main():
    # Example 1: Direct help
    print("\nExample 1: Direct help")
    result = await Runner.run(main_agent, "What is the weather like?")
    print(result.final_output)

    # Example 2: Escalation
    print("\nExample 2: Escalation")
    result = await Runner.run(main_agent, "I need to speak to a manager about a serious issue with my account.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())


