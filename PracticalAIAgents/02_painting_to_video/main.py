import asyncio
import argparse
from workflow import main

# https://www.metmuseum.org/art/collection/search/437127

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process artwork URL to generate image prompt and optional video")
    parser.add_argument(
        "--url", type=str, required=True,
        help="URL of the artwork page to process"
    )
    parser.add_argument(
        "--video", action="store_true",
        help="Generate video if this flag is set"
    )
    args = parser.parse_args()

    # Run the main workflow with video flag
    asyncio.run(main(args.url, args.video))
