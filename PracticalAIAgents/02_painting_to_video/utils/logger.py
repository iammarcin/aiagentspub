from config import DEBUG
import json
import structlog

logger = structlog.get_logger()


def log_result(result) -> None:
    """Helper function to log results from agent runs"""
    if DEBUG:
        logger.info("\n=== Agent Result ===")
        
        # Log final output
        if hasattr(result, 'final_output'):
            output = result.final_output
            if hasattr(output, 'model_dump'):
                try:
                    output_dict = output.model_dump()
                    logger.info(f"Final Output: {json.dumps(output_dict, indent=2)}")
                except Exception as e:
                    logger.error(f"Error serializing output: {str(e)}")
                    logger.error(f"Final Output: {output}")
            else:
                if isinstance(output, str) and len(output) > 200:
                    logger.info(f"Final Output: {output[:200]}...")
                else:
                    logger.info(f"Final Output: {output}")
