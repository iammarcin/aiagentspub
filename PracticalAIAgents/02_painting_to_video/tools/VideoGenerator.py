#VideoGenerator.py
import traceback
import structlog
import time
import os
import asyncio
import PIL.Image

from utils.file_storage_utils import FileStorage
from google.genai import types
from google import genai

logger = structlog.get_logger()

class GeminiVideoGenerator:
    def __init__(self):
        self.number_of_videos = 1  # Default as per docs: between 1 and 2 videos
        self.model = "veo-2.0-generate-001"  # Default Veo 2 model as per the docs
        self.aspect_ratio = "9:16"
        self.person_generation = "allow_adult" # "dont_allow"  # Default is dont_allow for safety
        self.duration_seconds = 5  # Default duration 5 seconds, can be between 5-8
        self.enhance_prompt = True
        self.video_mode = None  # text2video or img2video
        # Instantiate the Gemini client with API key
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            # Log error and potentially raise a more specific configuration error
            logger.error("GOOGLE_API_KEY environment variable not set.")
            raise ValueError("GOOGLE_API_KEY must be set in environment variables.")
        self.client = genai.Client(
            api_key=api_key,
            #http_options={"api_version": "v1alpha"}
        )
        # Instantiate the FileStorage utility
        self.file_storage = FileStorage()

    async def generate(self, prompt: str, image_path: str | None = None) -> str | None:
        """
        Generates a video based on a text prompt and an optional input image path.
        Uses instance attributes for configuration parameters.

        Args:
            prompt: The text prompt for video generation.
            image_path: Optional path to a local image file for image-to-video generation.

        Returns:
            The local path to the generated video file, or None if generation failed.
        """
        try:
            if not prompt:
                logger.error("GeminiVideoGenerator: Prompt is required")
                return None

            image_prompt_pil = None
            video_mode = "text2video"
            # Process input image if path is provided
            if image_path:
                try:
                    if not os.path.exists(image_path):
                        logger.error(f"GeminiVideoGenerator: Input image path does not exist: {image_path}")
                        return None
                    image_prompt_pil = PIL.Image.open(image_path)
                    video_mode = "img2video"
                    logger.info(f"GeminiVideoGenerator: Using input image from path: {image_path} for {video_mode}")
                    # Build API Image object from file
                    api_image = types.Image.from_file(location=image_path)
                except Exception as e:
                    logger.error(f"Error processing input image file: {str(e)}")
                    traceback.print_exc()
                    return None

            # Track the async operation
            operation: genai.Operation
            if image_prompt_pil:
                # Image-to-video generation
                config = types.GenerateVideosConfig(
                    aspect_ratio=self.aspect_ratio,
                    number_of_videos=self.number_of_videos,
                    duration_seconds=self.duration_seconds,
                )
                logger.info(f"GeminiVideoGenerator using model: {self.model}, mode: {video_mode}, config: {config}")
                logger.info("GeminiVideoGenerator: Initiating image-to-video generation")
                operation = self.client.models.generate_videos(
                    model=self.model,
                    prompt=prompt,
                    image=api_image,
                    config=config
                )
            else:
                # Text-to-video generation
                config = types.GenerateVideosConfig(
                    person_generation=self.person_generation,
                    aspect_ratio=self.aspect_ratio,
                    number_of_videos=self.number_of_videos,
                    duration_seconds=self.duration_seconds,
                    #enhance_prompt=self.enhance_prompt,
                )
                logger.info(f"GeminiVideoGenerator using model: {self.model}, mode: {video_mode}, config: {config}")
                logger.info("GeminiVideoGenerator: Initiating text-to-video generation")
                operation = self.client.models.generate_videos(
                    model=self.model,
                    prompt=prompt,
                    config=config
                )

            # Poll until operation is complete
            timeout = 600  # 10 minutes maximum wait time
            start_time = time.time()
            logger.info(f"GeminiVideoGenerator: Polling operation {operation.name} for completion...")

            while not operation.done:
                if time.time() - start_time > timeout:
                    logger.error(f"GeminiVideoGenerator: Video generation timed out after {timeout} seconds for operation {operation.name}")
                    # Attempt to cancel the operation (best effort)
                    try:
                        self.client.operations.cancel(operation)
                        logger.info(f"Attempted to cancel operation {operation.name}")
                    except Exception as cancel_err:
                        logger.error(f"Failed to cancel operation {operation.name}: {cancel_err}")
                    return None

                await asyncio.sleep(10)  # Use asyncio.sleep in async function
                # Refresh operation state
                try:
                    operation = self.client.operations.get(operation)
                    # Log progress if metadata available (optional, depends on API)
                    if operation.metadata and hasattr(operation.metadata, 'progress_percent'):
                         logger.info(f"GeminiVideoGenerator: Operation {operation.name} progress: {operation.metadata.progress_percent}%")
                    else:
                         logger.info(f"GeminiVideoGenerator: Polling operation status {operation.name} - not done yet")
                except Exception as get_op_err:
                    logger.error(f"Error refreshing operation status for {operation.name}: {get_op_err}")
                    # Potentially retry or fail based on error type
                    await asyncio.sleep(15) # Wait longer before next poll attempt after error

            logger.info(f"GeminiVideoGenerator: Operation {operation.name} completed in {time.time() - start_time:.2f} seconds")

            # Check for operation errors
            if operation.error:
                logger.error(f"GeminiVideoGenerator: Operation {operation.name} failed with error: {operation.error}")
                return None

            if not operation.response or not operation.response.generated_videos:
                # No videos created: capture detailed diagnostics
                response = operation.response
                logger.error(f"GeminiVideoGenerator: No videos generated for operation {operation.name}. Full response: {response}")
                # Log any RAI filter metadata if present
                rai_count = getattr(response, "rai_media_filtered_count", None)
                rai_reasons = getattr(response, "rai_media_filtered_reasons", None)
                if rai_count is not None:
                    logger.error(f"GeminiVideoGenerator: RAI media filtered count: {rai_count}")
                if rai_reasons:
                    logger.error(f"GeminiVideoGenerator: RAI media filtered reasons: {rai_reasons}")
                # Check for operation error payload
                if operation.error:
                    logger.error(f"GeminiVideoGenerator: Operation error details: {operation.error}")
                return None

            # Process the first generated video
            generated_video = operation.response.generated_videos[0]
            # Use the remote URI for logging since Video has no .name attribute
            video_uri = generated_video.video.uri or '<unknown video URI>'
            logger.info(f"GeminiVideoGenerator: Downloading video from: {video_uri}")

            # Download the video bytes
            try:
                self.client.files.download(file=generated_video.video)
                # Use the correct field for bytes
                video_bytes = generated_video.video.video_bytes
                if not video_bytes:
                    logger.error(f"GeminiVideoGenerator: Failed to download video bytes from {video_uri}")
                    return None
            except Exception as download_err:
                logger.error(f"GeminiVideoGenerator: Error downloading video from {video_uri}: {download_err}")
                return None

            # Save the first generated video locally
            local_path = self.file_storage.save_video(video_bytes, prompt)
            if local_path:
                logger.info(f"Generated video saved locally at: {local_path}")
                return local_path
            else:
                logger.error("Failed to save video locally using FileStorage")
                return None

        except Exception as e:
            logger.error("Unhandled error in generate_video (GeminiVideoGenerator)")
            logger.error(str(e))
            traceback.print_exc()
            return None
