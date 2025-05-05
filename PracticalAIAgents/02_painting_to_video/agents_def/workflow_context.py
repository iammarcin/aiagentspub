# path=openai/PracticalAIAgents/02/agents_def/workflow_context.py
from dataclasses import dataclass

@dataclass
class WorkflowContext:
    """Context for the workflow run, including flags."""
    generate_video: bool 