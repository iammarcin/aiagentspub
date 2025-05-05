import os
import datetime
import base64
import uuid
import requests
from PIL import Image
from io import BytesIO

from pathlib import Path
import structlog
from utils.postprocessing import normalize_url

logger = structlog.get_logger()

class FileStorage:
    def __init__(self):
        # Create base directories if they don't exist
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.outputs_dir = os.path.join(self.base_dir, "outputs")
        self.images_dir = os.path.join(self.outputs_dir, "images")
        self.videos_dir = os.path.join(self.outputs_dir, "videos")
        
        self._ensure_dirs_exist()
    
    def _ensure_dirs_exist(self):
        """Ensure all required directories exist."""
        for dir_path in [self.outputs_dir, self.images_dir, self.videos_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"Created directory: {dir_path}")
    
    def _generate_filename(self, prefix="file", extension=""):
        """Generate a unique filename with timestamp and UUID."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{unique_id}{extension}"
    
    def download_image(self, image_url):
        """
        Download an image from a URL and save it to the local filesystem.
        
        Args:
            image_url: URL of the image to download
        
        Returns:
            filepath: Path to the downloaded image
        """
        try:
            # Skip if already a data URL
            if image_url.startswith("data:"):
                return image_url
            
            # Normalize the URL before downloading
            normalized_url = normalize_url(image_url)
            logger.debug(f"Normalized URL: {normalized_url}")
                
            # Request the image
            response = requests.get(normalized_url, stream=True)
            response.raise_for_status()
            
            # Determine extension from content type
            content_type = response.headers.get("content-type", "image/jpeg")
            ext = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/webp": ".webp",
                "image/gif": ".gif"
            }.get(content_type, ".jpg")
            
            # Save the image
            image_bytes = response.content
            filepath = self.save_image(image_bytes, extension=ext)
            
            logger.info(f"Downloaded image from {normalized_url} to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {str(e)}")
            return None
    
    def encode_image_to_base64(self, image_path):
        """
        Encode an image file to base64 with appropriate MIME type.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            data_url: Base64 encoded image as a data URL
        """
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                
            # Determine MIME type based on file extension
            ext = Path(image_path).suffix.lower()
            mime_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".gif": "image/gif"
            }.get(ext, "image/jpeg")
            
            encoded = base64.b64encode(image_data).decode("utf-8")
            data_url = f"data:{mime_type};base64,{encoded}"
            
            logger.debug(f"Encoded image {image_path} to base64")
            return data_url
            
        except Exception as e:
            logger.error(f"Failed to encode image to base64: {str(e)}")
            return None
    
    def save_image(self, image_bytes, prompt=None, extension=".png"):
        """
        Save an image to the local filesystem.
        
        Args:
            image_bytes: The image data as bytes
            prompt: Optional prompt text to save alongside the image
            extension: File extension (default: .png)
            
        Returns:
            filepath: The path to the saved image
        """
        try:
            # Generate a unique filename
            filename = self._generate_filename("image", extension)
            filepath = os.path.join(self.images_dir, filename)
            
            # Save the image
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            # Save the prompt if provided
            if prompt:
                prompt_filepath = os.path.join(self.images_dir, f"{filename}.txt")
                with open(prompt_filepath, "w") as f:
                    f.write(prompt)
            
            logger.info(f"Image saved successfully to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            return None
    
    def save_video(self, video_bytes, prompt=None, extension=".mp4"):
        """
        Save a video to the local filesystem.
        
        Args:
            video_bytes: The video data as bytes
            prompt: Optional prompt text to save alongside the video
            extension: File extension (default: .mp4)
            
        Returns:
            filepath: The path to the saved video
        """
        try:
            # Generate a unique filename
            filename = self._generate_filename("video", extension)
            filepath = os.path.join(self.videos_dir, filename)
            
            # Save the video
            with open(filepath, "wb") as f:
                f.write(video_bytes)
            
            # Save the prompt if provided
            if prompt:
                prompt_filepath = os.path.join(self.videos_dir, f"{filename}.txt")
                with open(prompt_filepath, "w") as f:
                    f.write(prompt)
            
            logger.info(f"Video saved successfully to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save video: {str(e)}")
            return None 