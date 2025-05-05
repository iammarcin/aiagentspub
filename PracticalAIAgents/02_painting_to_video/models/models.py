from typing import Optional
from pydantic import BaseModel, Field

class ArtworkImageURL(BaseModel):
    """Model for storing artwork image URLs"""
    main_image_url: Optional[str] = Field(None, description="Main image URL of the artwork")
    source_url: Optional[str] = Field(None, description="Original source URL where the artwork was found")

class ArtworkDetails(BaseModel):
    """Model for storing artwork details"""
    title: Optional[str] = Field(None, description="Title of the artwork")
    artist: Optional[str] = Field(None, description="Artist name")
    medium: Optional[str] = Field(None, description="Medium used (e.g., oil on canvas)")
    description: Optional[str] = Field(None, description="Description or details about the artwork")
    image_urls: ArtworkImageURL = Field(..., description="URLs related to the artwork")

class GeneratedPrompt(BaseModel):
    """Model for storing generated image prompt"""
    artwork_details: ArtworkDetails = Field(..., description="Original artwork details")
    prompt: str = Field(..., description="Generated prompt for image generation")
    source_url: str = Field(..., description="Source URL of the original artwork")

class ProcessingResult(BaseModel):
    """Model for storing the complete processing result"""
    artwork_details: ArtworkDetails = Field(..., description="Details of the original artwork")
    generated_prompt: str = Field(..., description="Generated prompt for image generation")
    generated_image_path: Optional[str] = Field(None, description="Local path to the generated image")
    generated_video_path: Optional[str] = Field(None, description="Local path to the generated video")
    error: Optional[str] = Field(None, description="Error message if processing failed") 