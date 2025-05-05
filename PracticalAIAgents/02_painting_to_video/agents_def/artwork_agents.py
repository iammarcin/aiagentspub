from agents import Agent, Runner
from typing import Optional
import structlog

from models.models import ArtworkDetails
from tools.crawl import crawl_artwork_url
from utils.logger import log_result

logger = structlog.get_logger()

# Agent for extracting artwork details
details_extractor_agent = Agent(
    name="Artwork Details Extractor",
    instructions="""
    You're tasked with extracting detailed information about an artwork from its webpage.
    
    Given an artwork's webpage URL, you should:
    1. Fetch the content using crawl_artwork_url
    2. Extract the following information:
       - Title of the artwork
       - Artist name
       - Medium/materials used
       - Description or details about the artwork
       - Image URLs (main image and source URL)
    
    Guidelines:
    - Extract ONLY information that is explicitly present in the content
    - NEVER make up or hallucinate information
    - Set fields to null if information isn't available
    - Be precise with dates, titles, and artist names
    - Include any relevant historical or contextual information in the description
    
    Return the information in the proper structured format using ArtworkDetails model.
    """,
    tools=[crawl_artwork_url],
    output_type=ArtworkDetails,
    model="gpt-4o-mini"
)

async def extract_artwork_details(artwork_url: str) -> Optional[ArtworkDetails]:
    """
    Extract detailed information about an artwork from its webpage
    
    Args:
        artwork_url: URL of the artwork page
        
    Returns:
        ArtworkDetails object with artwork information
    """
    logger.debug(f"Extracting artwork details from: {artwork_url}")
    
    try:
        result = await Runner.run(
            details_extractor_agent,
            f"Extract all details from this artwork page: {artwork_url}",
        )
        
        log_result(result)
        artwork_details = result.final_output
        
        return artwork_details
    except Exception as e:
        logger.error(f"Error extracting artwork details: {str(e)}")
        return None
