import os
from typing import Dict, Any, Optional
from openai import OpenAI
import structlog
from utils.file_storage_utils import FileStorage

logger = structlog.get_logger()

class TextGenerator:
    """
    A class for generating text content using OpenAI models with support for image inputs
    """
    
    def __init__(self):
        """Initialize the text generator with default settings"""
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Default settings
        self.model = "gpt-4o-mini"
        self.temperature = 0.7
        
        # Initialize FileStorage for image handling
        self.file_storage = FileStorage()

    def set_settings(self, user_settings: Dict[str, Any] = {}):
        """
        Configure the text generator with user-specified settings
        
        Args:
            user_settings: Dictionary containing configuration options
        """
        if user_settings:
            text_settings = user_settings.get("text", {})
            
            if "model" in text_settings:
                self.model = text_settings["model"]
                
            if "temperature" in text_settings:
                self.temperature = float(text_settings["temperature"])

    async def generate(self, system_prompt: str, user_message: str, image_url: Optional[str] = None, detail: str = "auto") -> str:
        """
        Generate a text response using OpenAI's Response API, optionally with an image input
        
        Args:
            system_prompt: Instructions for the AI model
            user_message: The user's input message
            image_url: Optional URL or path to an image to include in the request
            detail: Detail level for image processing ('low', 'high', or 'auto')
            
        Returns:
            Generated text response
        """
        logger.debug(f"Generating text response using model: {self.model}")
        
        try:
            # Handle text-only request (no image)
            if not image_url:
                response = self.client.responses.create(
                    model=self.model,
                    instructions=system_prompt,
                    input=user_message,
                    temperature=self.temperature
                )
                
                text = response.output_text.strip()
                logger.debug(f"Generated text (preview): {text[:100]}...")
                return text
            
            # Process the image if provided
            image_data_url = None
            
            # Handle data URL, local file, or remote URL
            if image_url.startswith("data:"):
                # Already a data URL
                image_data_url = image_url
            elif os.path.exists(image_url):
                # Local file path - encode to base64
                image_data_url = self.file_storage.encode_image_to_base64(image_url)
            else:
                # Remote URL - download and encode
                local_path = self.file_storage.download_image(image_url)
                if local_path and not local_path.startswith("data:"):
                    image_data_url = self.file_storage.encode_image_to_base64(local_path)
                else:
                    # If download failed or returned a data URL already
                    image_data_url = local_path or image_url
            
            # Create content structure for the input
            content = [
                {"type": "input_text", "text": user_message}
            ]
            
            # Add image data if we have a valid URL
            if image_data_url:
                content.append({
                    "type": "input_image",
                    "image_url": image_data_url,
                    "detail": detail
                })
            
            # Create the input structure with role and content
            input_data = [{
                "role": "user",
                "content": content
            }]
            
            # Make the API call with image
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=input_data,
                temperature=self.temperature
            )
            
            # Extract and return the generated text
            text = response.output_text.strip()
            logger.debug(f"Generated text with image (preview): {text[:100]}...")
            return text
            
        except Exception as e:
            error_msg = f"Error generating text response: {str(e)}"
            logger.error(error_msg)
            return f"Failed to generate text: {error_msg}"

    