# Painting to Video Demo: Artwork Processing with AI Agents

This project demonstrates an end-to-end AI-driven pipeline that processes an artwork URL to extract metadata, generates a creative text prompt, uses Google's Gemini models to create a high-resolution image (and optionally a short video), and saves all outputs locally with detailed logging and structured outputs.

## Features

- Extract artwork metadata from a given URL.
- Generate a detailed creative prompt for AI-based image and video creation.
- Create images using `GeminiImageGenerator`.
- Optionally generate short videos with `GeminiVideoGenerator`.
- Save media and prompts locally with timestamped, UUID-based filenames.
- Configure workflows, model parameters, and content settings via `config.py`.
- Structured logging powered by `structlog`.

## Project Structure

```bash
PracticalAIAgents/02_painting_to_video/
├── agents_def/
│   ├── coordination_agent.py   # orchestrates workflow among agents
│   ├── workflow_context.py     # toggles video generation
│   ├── prompt_generator.py     # builds system/user messages
│   ├── prompt_agents.py        # crafts and refines prompts
│   ├── artwork_agents.py       # fetches and parses artwork metadata
│   ├── image_agents.py         # invokes GeminiImageGenerator
│   └── video_agents.py         # invokes GeminiVideoGenerator
├── utils/
│   ├── logger.py               # configures structlog logging
│   ├── postprocessing.py       # URL‐normalization helpers
│   ├── file_storage_utils.py   # download, encode & save media locally
│   └── outputs/
│       ├── images/             # generated images & prompts
│       └── videos/             # generated videos & prompts
├── config.py                   # global settings (models, debug, content limits)
├── workflow.py                 # orchestrator for the agentic workflow
├── main.py                     # CLI entry point
├── artwork_details.json        # sample JSON output
└── README.md                   # this file
```

## Prerequisites

- Python 3.9 or higher
- `pip`

## Installation

Navigate to the demo directory and install dependencies:

```bash
cd PracticalAIAgents/02_painting_to_video
pip install -r requirements.txt
```

Optionally, customize model and content settings in `config.py` and ensure any required AI service credentials are set in your environment.

## Usage

### Command-Line Interface

Run the demo by specifying an artwork URL. Use `--video` to include video generation.

```bash
python main.py --url 'https://artgallerytheone.com/products/shadow-of-liberty-copy' --video
```

### Programmatic Invocation

```python
import asyncio
from workflow import main

asyncio.run(main(
    artwork_url='https://artgallerytheone.com/products/shadow-of-liberty-copy',
    generate_video=True
))
```

## Workflow Details

1. Input validation and tracing span.
2. Agents coordination:
   - `ArtworkAgents` fetch metadata.
   - `PromptAgents` build a creative prompt.
   - `ImageAgents` and `VideoAgents` generate media.
3. Local storage under `utils/outputs/images` and `utils/outputs/videos`.
4. Structured logging of key steps and outcomes.

## Output

Generated media and prompt text files are stored under:

- `utils/outputs/images/`
- `utils/outputs/videos/`

Sample structured output is available in `artwork_details.json`.

## Contributing

Contributions are welcome. Open an issue or pull request in the main repository.

## License

See the root project `LICENSE` file for details. 