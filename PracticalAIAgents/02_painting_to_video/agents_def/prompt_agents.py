# path=openai/PracticalAIAgents/02/agents_def/prompt_agents.py
from agents import Agent, function_tool
from pydantic import BaseModel
import structlog
from tools.TextGenerator import TextGenerator
from models.models import ArtworkDetails
from config import PROMPT_MODEL, PROMPT_TEMPERATURE
from agents_def.prompt_generator import generate_image_prompt as generate_image_prompt_impl, generate_video_prompt as generate_video_prompt_impl

logger = structlog.get_logger()

# Initialize TextGenerator with configuration
text_generator = TextGenerator()
text_generator.model = PROMPT_MODEL
text_generator.temperature = PROMPT_TEMPERATURE

class PromptGenerationOutput(BaseModel):
    """Model for storing the generated prompt"""
    prompt: str

# Model for storing the generated video prompt
class PromptVideoGenerationOutput(BaseModel):
    """Model for storing the generated video prompt"""
    prompt: str

@function_tool(name_override="generate_prompt")
async def generate_prompt_tool(artwork_details: ArtworkDetails) -> PromptGenerationOutput:
    """
    Generate an image prompt using the prompt_generator implementation and return the prompt.
    """
    prompt = await generate_image_prompt_impl(artwork_details, text_generator)
    if not prompt:
        logger.error("Prompt generation failed for artwork details: %s", artwork_details)
        raise ValueError("Failed to generate prompt")
    return PromptGenerationOutput(prompt=prompt)

@function_tool(name_override="generate_video_prompt")
async def generate_video_prompt_tool(
    artwork_details: ArtworkDetails,
    image_path: str,
    image_prompt: str
) -> PromptVideoGenerationOutput:
    """
    Generate a video prompt using the prompt_generator implementation, based on artwork details, the generated image, and the image prompt, then return the video prompt.
    """
    # Call the implementation with full context for more accurate video prompts
    prompt = await generate_video_prompt_impl(
        artwork_details,
        text_generator,
        image_url=image_path,
        image_prompt=image_prompt
    )
    if not prompt:
        logger.error("Video prompt generation failed for artwork details: %s, image_path: %s, image_prompt: %s", artwork_details, image_path, image_prompt)
        raise ValueError("Failed to generate video prompt")
    return PromptVideoGenerationOutput(prompt=prompt)


# Agent wrapping the prompt generation tool
prompt_generator_agent = Agent(
    name="Prompt Generator",
    instructions="Receive artwork details and use the generate_prompt tool to produce a detailed image prompt.",
    tools=[generate_prompt_tool],
    output_type=PromptGenerationOutput,
    model="gpt-4o-mini"
)


# Agent wrapping the video prompt generation tool
video_prompt_generator_agent = Agent(
    name="Video Prompt Generator",
    instructions="Receive artwork details and use the generate_video_prompt tool to produce a detailed video prompt.",
    tools=[generate_video_prompt_tool],
    output_type=PromptVideoGenerationOutput,
    model="gpt-4o-mini"
) 