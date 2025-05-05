import re
import structlog

from agents import function_tool
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

logger = structlog.get_logger()

@function_tool
async def crawl_artwork_url(url: str) -> str:
    """
    Fetches and scrapes content from an artwork URL using crawl4ai
    
    Args:
        url: The URL to fetch and scrape
        
    Returns:
        The cleaned content from the URL
    """
    logger.debug(f"Crawling URL: {url}")
    
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(),
        excluded_tags=["header", "script", "style", "footer", "nav", "menu"]
    )
    
    try:
        async with AsyncWebCrawler() as crawler:
            # Ensure proper awaiting of the crawler run
            result = await crawler.arun(url=url, config=config)
            
            if result.success:
                # Use cleaned_html which has better structure than extraction
                content = result.cleaned_html
                
                # Clean up the content
                content = re.sub(r'</(div|li|ul|p|span)>', '', content)
                content = re.sub(r'<(div|li|ul|p|span)[^>]*>', '', content)
                content = re.sub(r'\n\s*\n', '\n', content)
                
                # Extract image URLs
                img_urls = re.findall(r'<img[^>]+src="([^"]+)"', content)
                if img_urls:
                    logger.debug(f"Found {len(img_urls)} image URLs")
                    content += "\nImage URLs found:\n" + "\n".join(img_urls)
                
                # Limit content length if needed
                if len(content) > 2500:
                    content = content[:2500]
                
                logger.debug(f"Crawled content length: {len(content)}")
                logger.debug(f"Content preview: {content[:2000]}...")
                
                return content
            else:
                error_msg = f"Failed to crawl URL: {result.error_message}"
                logger.error(error_msg)
                return error_msg
    except Exception as e:
        error_msg = f"Error crawling URL: {str(e)}"
        logger.error(error_msg)
        return error_msg 