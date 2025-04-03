import json

from typing_extensions import TypedDict, Any

from agents import Agent, FunctionTool, RunContextWrapper, function_tool

# IDEA HERE IS TO show how to use functions as tools
# this is copy paste from openai documentation
# IMPORTANT! documentation and params for functions are used by LLM to call the function
'''
from docs:
You can use any Python function as a tool. The Agents SDK will setup the tool automatically:

The name of the tool will be the name of the Python function (or you can provide a name)
Tool description will be taken from the docstring of the function (or you can provide a description)
The schema for the function inputs is automatically created from the function's arguments
Descriptions for each input are taken from the docstring of the function, unless disabled
We use Python's inspect module to extract the function signature, along with griffe to parse docstrings and pydantic for schema creation.
'''

class Location(TypedDict):
    lat: float
    long: float

@function_tool  
async def fetch_weather(location: Location) -> str:
    
    """Fetch the weather for a given location.

    Args:
        location: The location to fetch the weather for.
    """
    # In real life, we'd fetch the weather from a weather API
    return "sunny"


@function_tool(name_override="fetch_data")  
def read_file(ctx: RunContextWrapper[Any], path: str, directory: str | None = None) -> str:
    """Read the contents of a file.

    Args:
        path: The path to the file to read.
        directory: The directory to read the file from.
    """
    # In real life, we'd read the file from the file system
    return "<file contents>"


agent = Agent(
    name="Assistant",
    tools=[fetch_weather, read_file],  
)

for tool in agent.tools:
    if isinstance(tool, FunctionTool):
        print(tool.name)
        print(tool.description)
        print(json.dumps(tool.params_json_schema, indent=2))
        print()