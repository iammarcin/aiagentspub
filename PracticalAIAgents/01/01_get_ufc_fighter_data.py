import asyncio
import json
import re
from typing import Optional

from pydantic import BaseModel, Field

from agents import Agent, Runner, trace, WebSearchTool, function_tool

# Import crawl4ai for web scraping
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Set to True for detailed debug output
DEBUG = True

# Pydantic models for structured data
class UFCFighterData(BaseModel):
    weightClass: Optional[str] = Field(None, description="Fighter's weight class or division")
    record: Optional[str] = Field(None, description="Fight record in format wins-losses-draws")
    nextFightDate: Optional[str] = Field(None, description="Date of next scheduled fight")
    nextFightOpponent: Optional[str] = Field(None, description="Opponent for next scheduled fight")
    headshotImageURL: Optional[str] = Field(None, description="URL to fighter's headshot image")
    fullBodyImageURL: Optional[str] = Field(None, description="URL to fighter's full body image")

class FighterURLs(BaseModel):
    ufc_url: Optional[str] = Field(None, description="URL to fighter's UFC profile")

class FighterDetailsResult(BaseModel):
    name: str = Field(..., description="Name of the fighter")
    ufc_data: Optional[UFCFighterData] = None

# Function to validate UFC URL
@function_tool
def validate_ufc_url(url: str) -> bool:
    """
    Validates if the provided URL is from the UFC domain
    
    Args:
        url: The URL to validate
        
    Returns:
        True if the URL is valid UFC URL, False otherwise
    """
    pattern = r'^https?://(?:www\.)?ufc\.com/athlete/[^/\s]+$'
    result = bool(re.match(pattern, url))
    if DEBUG:
        print(f"Validating UFC URL: {url} -> {result}")
    return result

# CrawlAI web scraping function tool
@function_tool
async def crawl_url(url: str) -> str:
    """
    Fetches and scrapes content from a URL using crawl4ai
    
    Args:
        url: The URL to fetch and scrape
        
    Returns:
        The cleaned content from the URL
    """
    if DEBUG:
        print(f"Crawling URL: {url}")
    
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(),
        excluded_tags=["header", "script", "style", "footer", "nav"]
    )
    
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            
            if result.success:
                # Use cleaned_html which has better structure than markdown for extraction
                content = result.cleaned_html
                
                # Clean up the content by removing unnecessary HTML tags
                content = re.sub(r'</(div|li|ul|p|span)>', '', content)
                content = re.sub(r'<(div|li|ul|p|span)[^>]*>', '', content)
                # Remove empty lines
                content = re.sub(r'\n\s*\n', '\n', content)
                
                # Limit content length if needed
                if len(content) > 2500:
                    content = content[:2500]
                
                if DEBUG:
                    print(f"Crawled content length: {len(content)}")
                    print(f"Content preview: {content[:500]}...")
                
                return content
            else:
                error_msg = f"Failed to crawl URL: {result.error_message}"
                if DEBUG:
                    print(error_msg)
                return error_msg
    except Exception as e:
        error_msg = f"Error crawling URL: {str(e)}"
        if DEBUG:
            print(error_msg)
        return error_msg

# Helper function to log tool calls and results
def log_tool_call(name, args=None):
    if DEBUG:
        print(f"\n> Tool Called: {name}")
        if args:
            print(f"> Args: {args}")

def log_tool_result(result):
    if DEBUG:
        if isinstance(result, str) and len(result) > 200:
            print(f"> Tool Result: {result[:200]}...")
        else:
            print(f"> Tool Result: {result}")

# Debug function to inspect result
def log_result(phase, result):
    if DEBUG:
        print(f"\n=== {phase} Result ===")
        
        # Log new items that were generated
        if hasattr(result, 'new_items'):
            print(f"Generated {len(result.new_items)} new items:")
            for i, item in enumerate(result.new_items):
                try:
                    if item.type == "tool_call_item":
                        print(f"  Tool Call #{i}: ", end="")
                        # Handle different tool call structures
                        if hasattr(item.raw_item, 'name'):
                            print(item.raw_item.name)
                            if hasattr(item.raw_item, 'arguments'):
                                print(f"    Arguments: {item.raw_item.arguments}")
                        elif hasattr(item.raw_item, 'function'):
                            print(item.raw_item.function.name)
                            if hasattr(item.raw_item.function, 'arguments'):
                                print(f"    Arguments: {item.raw_item.function.arguments}")
                        else:
                            print(f"Unknown tool structure: {type(item.raw_item)}")
                    elif item.type == "tool_call_output_item":
                        output = str(item.output) if hasattr(item, 'output') else str(item.raw_item.get('output', ''))
                        if len(output) > 100:
                            output = output[:100] + "..."
                        print(f"  Tool Output #{i}: {output}")
                except Exception as e:
                    print(f"  Error logging item #{i}: {str(e)}")
        
        # Log final output
        if hasattr(result, 'final_output'):
            output = result.final_output
            if isinstance(output, (dict, BaseModel)):
                try:
                    if hasattr(output, 'model_dump'):
                        output = output.model_dump()
                    print(f"Final Output: {json.dumps(output, indent=2)}")
                except:
                    print(f"Final Output: {output}")
            else:
                if isinstance(output, str) and len(output) > 200:
                    print(f"Final Output: {output[:200]}...")
                else:
                    print(f"Final Output: {output}")

async def run(fighter_name: str):
    # 1. URL Finder Agent - Finds URLs for UFC profiles
    url_finder_agent = Agent(
        name="UFC Fighter URL Finder",
        instructions="""
        You're tasked with finding the official profile URL for UFC fighters.
        For any given fighter name, search for and return their profile URL from the UFC website.
        
        You MUST return the URL in the proper structured format.
        Only include direct profile URLs, not search results or unrelated pages.
        
        For UFC URLs: They should match the pattern https://www.ufc.com/athlete/[fighter-name]
        
        If you cannot find a URL, return null for that field.
        NEVER make up URLs or hallucinate data. If you can't find a URL, set the field to null.
        
        After finding the URL, make sure to validate it using the validate_ufc_url tool.
        """,
        tools=[WebSearchTool(), validate_ufc_url],
        output_type=FighterURLs,
        model="gpt-4o-mini"
    )

    # 2. UFC Fetch and Extract Agent
    ufc_fetch_extract_agent = Agent(
        name="UFC Data Fetch and Extract Agent",
        instructions="""
        You're tasked with fetching and extracting fighter information from UFC.com.
        
        Given a fighter's UFC profile URL, you should:
        1. Fetch the content using the crawl_url tool
        2. Extract ONLY the following information from the fetched content:
           - Weight Class / Division
           - Fight Record (wins-losses-draws)
           - Next Fight Date (if available)
           - Next Fight Opponent (if available) 
           - Headshot Image URL (if available)
           - Full Body Image URL (if available)
        
        ONLY extract data that is EXPLICITLY present in the content.
        NEVER hallucinate or make up information that isn't present.
        Set fields to null if information can't be found.
        
        Return ONLY the extracted data in valid JSON format according to the UFCFighterData model.
        DO NOT include any explanations or commentary.
        """,
        tools=[crawl_url],
        model="gpt-4o-mini",
        output_type=UFCFighterData
    )

    print(f"\n{'='*50}")
    print(f"Starting data collection for UFC fighter: {fighter_name}")
    print(f"{'='*50}\n")

    # Step 1: Find the URL
    print("Step 1: Finding fighter URL...")
    try:
        print(f"Searching for fighter: {fighter_name}")
        url_result = await Runner.run(
            url_finder_agent,
            f"Find the official profile URL for UFC fighter {fighter_name}",
        )
        
        log_result("URL Finder", url_result)
        
        urls = url_result.final_output
        print(f"Found URL: {urls.ufc_url}")
    except Exception as e:
        print(f"Error finding URL: {str(e)}")
        return FighterDetailsResult(name=fighter_name)
    
    # Step 2: Fetch and Extract UFC data
    fighter_data = FighterDetailsResult(name=fighter_name)
    
    if urls.ufc_url:
        try:
            print(f"\nStep 2: Fetching and extracting UFC data from: {urls.ufc_url}")
            ufc_result = await Runner.run(
                ufc_fetch_extract_agent,
                f"Fetch and extract data from this UFC URL: {urls.ufc_url}",
            )
            
            log_result("UFC Fetch and Extract", ufc_result)
            
            fighter_data.ufc_data = ufc_result.final_output
            print(f"UFC data extracted: {json.dumps(fighter_data.ufc_data.model_dump(), indent=2)}")
        except Exception as e:
            print(f"Error with UFC data: {str(e)}")
            fighter_data.ufc_data = UFCFighterData()
    else:
        print("No UFC URL found, skipping UFC data extraction.")
    
    # Return the final structured data
    print("\nFinal Result:")
    print(json.dumps(fighter_data.model_dump(), indent=2))
    
    return fighter_data

async def main():
    # Define the fighter name you want to retrieve data for
    fighter_name = "Alexander Volkanovski"
    
    # Run without MCP server
    try:
        with trace(workflow_name="UFC Fighter Data Collection"):
            result = await run(fighter_name)
            
            # Save the results to a JSON file
            output_file = f"{fighter_name.replace(' ', '_')}_data.json"
            with open(output_file, "w") as f:
                json.dump(result.model_dump(), f, indent=2)
            
            print(f"\nData saved to {output_file}")
    except Exception as e:
        print(f"Critical error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
