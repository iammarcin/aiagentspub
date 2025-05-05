#ImageGenerator.py

import traceback

import requests
import os

from utils.file_storage_utils import FileStorage
import structlog
from google.genai import types
from google import genai
logger = structlog.get_logger()

class GeminiImageGenerator:
    def __init__(self):
        self.number_of_images = 1  # Default as per docs: generate between 1 and 4 images, default is 4.
        self.model = "imagen-3.0-generate-002"
        self.aspect_ratio = "9:16"
        # Instantiate the Gemini client with API key
        self.client = genai.Client(
            api_key=os.environ.get("GOOGLE_API_KEY"),
            http_options={"api_version": "v1alpha"}
        )
        # Instantiate the FileStorage utility
        self.file_storage = FileStorage()

    async def generate(self, image_prompt: str):
        try:
            if image_prompt is None:
                logger.error("GeminiImageGenerator: image_prompt is required")
                return None

            test_mode = False
            if test_mode:
                logger.info("GeminiImageGenerator: test_mode")
                # Return test data if enabled
                finalUrl = "https://myaiappess3bucketnonprod.s3.eu-south-2.amazonaws.com/1/assets/chat/1/20241130_fd938d0c_tmp9edokoto.png"
                # Also save it locally if it's a valid URL
                try:
                    response = requests.get(finalUrl)
                    response.raise_for_status()
                    local_path = self.file_storage.save_image(response.content, prompt)
                except Exception as e:
                    logger.error(f"Failed to save test image locally: {str(e)}")
            else:
                logger.info("GeminiImageGenerator: image_prompt %s", image_prompt)

                # Prepare configuration for the Gemini generate_images call
                config = types.GenerateImagesConfig(
                    number_of_images=self.number_of_images,
                    aspect_ratio=self.aspect_ratio
                )

                # Call the Gemini API to generate images
                response = self.client.models.generate_images(
                    model=self.model,
                    prompt=image_prompt,
                    config=config
                )

                if not response.generated_images:
                    logger.error("GeminiImageGenerator: No images generated")
                    return None
                generated_image = response.generated_images[0]
                image_bytes = generated_image.image.image_bytes

                # Save the generated image locally
                local_path = self.file_storage.save_image(image_bytes, image_prompt)

            if local_path:
                logger.info(f"Generated image saved locally at: {local_path}")
                return local_path
            else:
                logger.error("GeminiImageGenerator: Failed to save image locally")
                return None

        except Exception as e:
            logger.error("Error in generate_image (GeminiImageGenerator)")
            logger.error(e)
            traceback.print_exc()
            return None
