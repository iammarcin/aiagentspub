# path=openai/PracticalAIAgents/02/agents_def/video_agents.py
from agents import Agent, function_tool
from pydantic import BaseModel
import structlog
from tools.VideoGenerator import GeminiVideoGenerator

logger = structlog.get_logger()

# Initialize the GeminiVideoGenerator
video_generator = GeminiVideoGenerator()

class VideoGenerationOutput(BaseModel):
    """Model for storing the path of the generated video"""
    video_path: str

@function_tool(name_override="generate_video")
async def generate_video_tool(prompt: str, image_path: str) -> VideoGenerationOutput:
    """
    Generate a video based on the prompt and optional image using GeminiVideoGenerator and return the video path.
    """
    video_path = await video_generator.generate(prompt=prompt, image_path=image_path)
    if not video_path:
        logger.error("Video generation failed for prompt: %s", prompt)
        raise ValueError("Failed to generate video")
    return VideoGenerationOutput(video_path=video_path)

# Agent wrapping the video generation tool
video_generator_agent = Agent(
    name="Video Generator",
    instructions="Receive a detailed prompt and image path, use the generate_video tool to produce a video, then return the local path to the generated video.",
    tools=[generate_video_tool],
    output_type=VideoGenerationOutput,
    model="gpt-4o-mini"
) 