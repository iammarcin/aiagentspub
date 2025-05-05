import asyncio
from agents import trace, Runner
from config import WORKFLOW_NAME
from agents_def.coordination_agent import coordination_agent
import structlog
from agents_def.workflow_context import WorkflowContext

logger = structlog.get_logger()

async def main(artwork_url: str = None, generate_video: bool = False):
    """
    Main entry point for the artwork processing workflow
    
    Args:
        artwork_url: URL of the artwork page (optional, uses default if None)
        generate_video: Flag to generate video (optional, default is False)
    """
    # Default artwork URL if none provided
    if artwork_url is None:
        logger.error("No artwork URL provided. Using default URL.")
        # exit the program
        exit()
    
    try:
        with trace(workflow_name=WORKFLOW_NAME):
            # Agentic workflow orchestration
            user_input = f"URL: {artwork_url}"
            run_result = await Runner.run(
                coordination_agent,
                user_input,
                context=WorkflowContext(generate_video)
            )
            result = run_result.final_output
            logger.info("\nFinal Result Summary:")
            if result.error:
                logger.error(f"Error: {result.error}")
            else:
                ad = result.artwork_details
                logger.info(f"Processed: {ad.title} by {ad.artist}")
                logger.info(f"Generated prompt: {result.generated_prompt[:100]}...")
                logger.info(f"Generated image path: {result.generated_image_path}")
                logger.info(f"Generated video path: {result.generated_video_path}")
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 