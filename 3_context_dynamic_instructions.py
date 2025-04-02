from dataclasses import dataclass
from typing import List
import asyncio
from agents import Agent, Runner, function_tool, RunContextWrapper

# IDEA HERE IS TO show dynamic instructions based on the context
# here context of course is dummy data - but we can get it from the database etc

@dataclass
class UserContext:
    name: str
    preferences: List[str]
    subscription_tier: str
    
    async def get_user_preferences(self) -> List[str]:
        # In a real app, this might fetch from a database
        return self.preferences
    
    async def get_subscription_features(self) -> List[str]:
        # Dummy feature lists based on subscription tier
        features = {
            "free": ["basic chat", "limited responses"],
            "pro": ["advanced chat", "unlimited responses", "priority support"],
            "enterprise": ["all features", "dedicated support", "custom tools"]
        }
        return features.get(self.subscription_tier, [])

# Create a tool that uses our context
@function_tool
async def get_user_info(ctx: RunContextWrapper[UserContext]) -> str:
    preferences = await ctx.context.get_user_preferences()
    features = await ctx.context.get_subscription_features()
    
    return f"User preferences: {', '.join(preferences)}\nAvailable features: {', '.join(features)}"

# Define dynamic instructions function
def dynamic_instructions(
    context: RunContextWrapper[UserContext], 
    agent: Agent[UserContext]
) -> str:
    return f"""You are a personal assistant for {context.context.name}.
Their subscription tier is {context.context.subscription_tier}.
Please help them with their questions and requests.
Be extra attentive since they are a {context.context.subscription_tier} tier user.
Before responding greet them with their name.
"""

# Create our agent with dynamic instructions
agent = Agent[UserContext](
    name="Personal Assistant",
    instructions=dynamic_instructions,
    model="gpt-4o-mini",
    tools=[get_user_info]
)

async def main():
    # Create a user context with some dummy data
    user_context = UserContext(
        name="Alice",
        preferences=["technology", "science", "books"],
        subscription_tier="pro"
    )
    
    # Run the agent with our context
    result = await Runner.run(
        agent,
        "What are my preferences and available features?",
        context=user_context
    )
    
    print("Agent Response:")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())