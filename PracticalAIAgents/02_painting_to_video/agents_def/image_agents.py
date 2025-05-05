# path=openai/PracticalAIAgents/02/agents_def/image_agents.py
from agents import Agent, function_tool
from pydantic import BaseModel
import structlog
from tools.ImageGenerator import GeminiImageGenerator

logger = structlog.get_logger()

# Initialize the GeminiImageGenerator
image_generator = GeminiImageGenerator()

class ImageGenerationOutput(BaseModel):
    """Model for storing the path of the generated image"""
    image_path: str

@function_tool(name_override="generate_image")
async def generate_image_tool(prompt: str) -> ImageGenerationOutput:
    """
    Generate an image based on the prompt using GeminiImageGenerator and return the image path.
    """
    image_path = await image_generator.generate(prompt)
    if not image_path:
        logger.error("Image generation failed for prompt: %s", prompt)
        raise ValueError("Failed to generate image")
    return ImageGenerationOutput(image_path=image_path)

# Agent wrapping the image generation tool
image_generator_agent = Agent(
    name="Image Generator",
    instructions="Receive a detailed prompt and use the generate_image tool to produce an image, then return the local path to the generated image.",
    tools=[generate_image_tool],
    output_type=ImageGenerationOutput,
    model="gpt-4o-mini"
) 