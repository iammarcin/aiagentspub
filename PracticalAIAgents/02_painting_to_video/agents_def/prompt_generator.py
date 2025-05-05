from typing import Dict, Any, Optional

from models.models import ArtworkDetails
from tools.TextGenerator import TextGenerator
from utils.postprocessing import normalize_url
import structlog

logger = structlog.get_logger()

async def generate_image_prompt(artwork_details: ArtworkDetails, text_generator: TextGenerator) -> str:
    """
    Generate a detailed prompt for image generation based on artwork details using TextGenerator
    
    Args:
        artwork_details: The artwork details including title, artist, description, and image URL
        text_generator: Initialized TextGenerator instance to use for prompt generation
        
    Returns:
        A detailed prompt for image generation
    """
    logger.debug(f"Generating image prompt for artwork: {artwork_details.title}")
    
    # Construct a detailed system prompt
    system_prompt = """
    You're a prompt engineering expert specializing in creating detailed image generation prompts 
    inspired by artwork. Analyze the artwork details and image provided, then create a 
    detailed prompt that:
    
    1. Captures the essence, style, and mood of the original
    2. Describes the subject matter, composition, and visual elements
    3. Specifies color palette, lighting, and atmosphere
    4. Includes artistic technique references (brushwork, texture, etc.)
    5. Adds creative extensions or interpretations that enhance the original concept
    
    Your prompt should be inspired by but not directly copy the original artwork.
    Don't mention the original artwork in the prompt in any way.
    Make the prompt detailed enough for a text-to-image model to create a high-quality image.
    """
    
    # Create the user message with artwork details
    user_message = f"""
    Create an inspiring, detailed image generation prompt based on this artwork:
    
    Title: {artwork_details.title or 'Unknown'}
    Artist: {artwork_details.artist or 'Unknown'}
    Medium: {artwork_details.medium or 'Unknown'}
    Description: {artwork_details.description or 'No description available'}
    
    Please provide a detailed, creative prompt that captures the essence of this artwork while adding your own creative extensions.
    """
    
    # Get the image URL from artwork details and normalize it
    image_url = None
    if artwork_details.image_urls and artwork_details.image_urls.main_image_url:
        raw_url = artwork_details.image_urls.main_image_url
        image_url = normalize_url(raw_url)
        logger.debug(f"Using normalized image URL: {image_url}")
    
    # Use the TextGenerator to generate the prompt, passing the image URL
    return await text_generator.generate(system_prompt, user_message, image_url)

async def generate_video_prompt(
    artwork_details: ArtworkDetails,
    text_generator: TextGenerator,
    image_url: Optional[str] = None,
    image_prompt: Optional[str] = None,
) -> str:
    """
    Generate a detailed prompt for video generation based on artwork details using TextGenerator
    
    Args:
        artwork_details: The artwork details including title, artist, description, and image URLs
        text_generator: Initialized TextGenerator instance to use for prompt generation
        image_url: The local path or URL of the generated image from step 3
        image_prompt: The image prompt string used to generate the image
        
    Returns:
        A detailed prompt for video generation
    """
    logger.debug(f"Generating video prompt for artwork: {artwork_details.title}")

    # Construct a detailed system prompt for video generation
    system_prompt = """
    <PROMPT_GUIDELINES>
    Prompt writing basics
Good prompts are descriptive and clear. To get your generated video as close as possible to what you want, start with identifying your core idea, and then refine your idea by adding keywords and modifiers.

The following elements should be included in your prompt:

Subject: The object, person, animal, or scenery that you want in your video.
Context: The background or context in which the subject is placed.
Action: What the subject is doing (for example, walking, running, or turning their head).
Style: This can be general or very specific. Consider using specific film style keywords, such as horror film, film noir, or animated styles like cartoon style.
Camera motion: [Optional] What the camera is doing, such as aerial view, eye-level, top-down shot, or low-angle shot.
Composition: [Optional] How the shot is framed, such as wide shot, close-up, or extreme close-up.
Ambiance: [Optional] How the color and light contribute to the scene, such as blue tones, night, or warm tones.
More tips for writing prompts
The following tips help you write prompts that generate your videos:

Use descriptive language: Use adjectives and adverbs to paint a clear picture for Veo.
Provide context: If necessary, include background information to help your model understand what you want.
Reference specific artistic styles: If you have a particular aesthetic in mind, reference specific artistic styles or art movements.
Utilize prompt engineering tools: Consider exploring prompt engineering tools or resources to help you refine your prompts and achieve optimal results. For more information, visit Introduction to prompt design.
    Enhance the facial details in your personal and group images: Specify facial details as a focus of the photo like using the word portrait in the prompt.

    Example prompts and output
    - Close up shot (composition) of melting icicles (subject) on a frozen rock wall (context) with cool blue tones (ambiance), zoomed in (camera motion) maintaining close-up detail of water drips (action).
    - A close-up cinematic shot follows a desperate man in a weathered green trench coat as he dials a rotary phone mounted on a gritty brick wall, bathed in the eerie glow of a green neon sign. The camera dollies in, revealing the tension in his jaw and the desperation etched on his face as he struggles to make the call. The shallow depth of field focuses on his furrowed brow and the black rotary phone, blurring the background into a sea of neon colors and indistinct shadows, creating a sense of urgency and isolation.
    - A video with smooth motion that dollies in on a desperate man in a green trench coat, using a vintage rotary phone against a wall bathed in an eerie green neon glow. The camera starts from a medium distance, slowly moving closer to the man's face, revealing his frantic expression and the sweat on his brow as he urgently dials the phone. The focus is on the man's hands, his fingers fumbling with the dial as he desperately tries to connect. The green neon light casts long shadows on the wall, adding to the tense atmosphere. The scene is framed to emphasize the isolation and desperation of the man, highlighting the stark contrast between the vibrant glow of the neon and the man's grim determination.
    - Create a short 3D animated scene in a joyful cartoon style. A cute creature with snow leopard-like fur, large expressive eyes, and a friendly, rounded form happily prances through a whimsical winter forest. The scene should feature rounded, snow-covered trees, gentle falling snowflakes, and warm sunlight filtering through the branches. The creature's bouncy movements and wide smile should convey pure delight. Aim for an upbeat, heartwarming tone with bright, cheerful colors and playful animation.
    </PROMPT_GUIDELINES>
    
    You're a prompt engineering expert specializing in creating detailed video generation prompts 
    inspired by artwork. Analyze <PROMPT_GUIDELINES>, the artwork details and create a  detailed prompt that:
    
    1. Describes the video storyline, motion, and transitions inspired by the artwork subject
    2. Specifies pacing, length, and key visual elements
    3. Includes style references (camera angles, effects, animation style)
    4. Adds creative narrative or dynamic elements to bring the artwork to life in a video
    5. Video will be 5 seconds long
    
    Your prompt should be inspired by but not directly copy the original artwork.
    Make the prompt detailed enough for a text-to-video model to create a high-quality video.
    """

    # Create the user message with artwork details and image context
    user_message = f"""
    Create a dynamic video generation prompt based on this artwork:
    
    Title: {artwork_details.title or 'Unknown'}
    Artist: {artwork_details.artist or 'Unknown'}
    Description: {artwork_details.description or 'No description available'}

    The generated image can be found at: {image_url or 'N/A'}
    It was created using the prompt: {image_prompt or 'N/A'}
    """

    # Use the TextGenerator to generate the video prompt, passing the image context
    return await text_generator.generate(system_prompt, user_message, image_url) 