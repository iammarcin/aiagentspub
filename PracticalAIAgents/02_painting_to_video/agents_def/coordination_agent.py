# path=openai/PracticalAIAgents/02/agents_def/coordination_agent.py
from agents import Agent, RunContextWrapper
from agents_def.artwork_agents import details_extractor_agent
from agents_def.prompt_agents import prompt_generator_agent, video_prompt_generator_agent
from agents_def.image_agents import image_generator_agent
from agents_def.video_agents import video_generator_agent
from models.models import ProcessingResult, ArtworkDetails
from agents_def.workflow_context import WorkflowContext

def dynamic_coordinator_instructions(ctx: RunContextWrapper[WorkflowContext], agent: Agent) -> str:
    """Generate instructions based on whether video generation is enabled in context"""
    generate_video = ctx.context.generate_video
    instructions = (
        "You are a workflow coordinator for processing artwork URLs. You will receive input in the format:\n"
        "\"URL: <artwork_url>\".\n\n"
        "Follow these steps in order:\n"
        "1. Call the extract_details tool with arguments artwork_url (string) to extract artwork details.\n"
        "2. Call the generate_prompt tool with the returned ArtworkDetails object to generate a detailed image prompt.\n"
        "3. Call the generate_image tool with the generated prompt string to generate an image and obtain image_path.\n"
    )
    if generate_video:
        instructions += (
            "4. Call the generate_video_prompt tool with arguments artwork_details (from step 1), image_path (from step 3), and generated_prompt (from step 2) to generate a detailed video prompt.\n"
            "5. Call the generate_video tool with arguments prompt (from step 4) and image_path (from step 3) to generate a video and obtain video_path.\n"
            "6. Return a ProcessingResult object containing:\n"
            "   - artwork_details: the ArtworkDetails from step 1\n"
            "   - generated_prompt: the prompt string from step 2\n"
            "   - generated_image_path: the image_path from step 3\n"
            "   - generated_video_path: the video_path from step 5\n"
        )
    else:
        instructions += (
            "4. Return a ProcessingResult object containing:\n"
            "   - artwork_details: the ArtworkDetails from step 1\n"
            "   - generated_prompt: the prompt string from step 2\n"
            "   - generated_image_path: the image_path from step 3\n"
            "   - generated_video_path: None\n"
        )
    return instructions

coordination_agent = Agent(
    name="Workflow Coordinator",
    instructions=dynamic_coordinator_instructions,
    tools=[
        details_extractor_agent.as_tool(
            tool_name="extract_details",
            tool_description="Extract artwork details given a URL"
        ),
        prompt_generator_agent.as_tool(
            tool_name="generate_prompt",
            tool_description="Generate a detailed image prompt from artwork details"
        ),
        image_generator_agent.as_tool(
            tool_name="generate_image",
            tool_description="Generate an image from a prompt"
        ),
        video_prompt_generator_agent.as_tool(
            tool_name="generate_video_prompt",
            tool_description="Generate a detailed video prompt from artwork details"
        ),
        video_generator_agent.as_tool(
            tool_name="generate_video",
            tool_description="Generate a video given a prompt and an image path"
        ),
    ],
    output_type=ProcessingResult,
    model="gpt-4.1"
) 