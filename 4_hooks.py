from dataclasses import dataclass
import asyncio
from agents import Agent, Runner, AgentHooks, RunContextWrapper, function_tool, enable_verbose_stdout_logging

#enable_verbose_stdout_logging()

# IDEA HERE IS TO show hooks
# so mainly there are 5 built in hooks - and we can trigger all kind of custom events depending on the process state
# BTW verbose logging is also useful.

@dataclass
class UserContext:
    name: str
    session_id: str

@function_tool
async def greet_user(ctx: RunContextWrapper[UserContext]) -> str:
    """Greet the user by name"""
    return f"Hello {ctx.context.name}!"

class CustomAgentHooks(AgentHooks[UserContext]):
    """
    Implements agent lifecycle hooks to demonstrate when they're called
    """
    
    async def on_start(self, ctx: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> None:
        print(f"\n[Hook] Agent {agent.name} starting")
        print(f"[Hook] User context: {ctx.context.name}, Session: {ctx.context.session_id}")

    async def on_end(self, ctx: RunContextWrapper[UserContext], agent: Agent[UserContext], output_data) -> None:
        print(f"\n[Hook] Agent {agent.name} finished")
        print(f"[Hook] Output: {output_data}")

    async def on_tool_start(self, ctx: RunContextWrapper[UserContext], agent: Agent[UserContext], tool) -> None:
        print(f"\n[Hook] Tool starting for {tool.name}")

    async def on_tool_end(self, ctx: RunContextWrapper[UserContext], agent: Agent[UserContext], tool, result) -> None:
        print(f"\n[Hook] Tool {tool.name} finished with output: {result}")

    async def on_handoff(self, ctx: RunContextWrapper[UserContext], agent: Agent[UserContext], source) -> None:
        print(f"\n[Hook] Handoff!")
        print(f"[Hook] Handoff source: {source}")


# Create a sub-agent for handoff demonstration
sub_agent = Agent[UserContext](
    name="SubAgent",
    instructions="You are a helpful sub-agent. Keep responses brief.",
    model="gpt-4o-mini",
    hooks=CustomAgentHooks()
)

# Create our main agent with hooks and handoff capability
main_agent = Agent[UserContext](
    name="MainAgent",
    instructions="""You are a helpful assistant.
    Use the greet_user tool to greet the user.
    If the user asks about delegation, use the handoff to the sub-agent.
    Explain your reasoning as you work.""",
    tools=[greet_user],
    handoffs=[sub_agent],
    model="gpt-4o-mini",
    hooks=CustomAgentHooks()
)

async def main():
    # Create user context
    user_context = UserContext(
        name="Alice",
        session_id="session_123"
    )
    
    print("=== First Run: Basic Tool Usage ===")
    result = await Runner.run(
        main_agent,
        "Please greet me!",
        context=user_context
    )
    
    print("\n=== Second Run: Handoff Example ===")
    result = await Runner.run(
        main_agent,
        "Can you delegate this task to handle a simple hello?",
        context=user_context
    )

if __name__ == "__main__":
    asyncio.run(main())
