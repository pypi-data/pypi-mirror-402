from fastmcp import FastMCP
from .api_client import YouMindAPIClient
from .exceptions import CraftNotFoundError, CraftAccessError, CraftContentError
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger(__name__)

mcp = FastMCP("YouMindMCP")
api_client = YouMindAPIClient()


@mcp.tool
def get_craft_content(craft_id: str) -> str:
    """
    Retrieve craft content by craft ID.
    
    Args:
        craft_id: The ID of the craft to retrieve
        
    Returns:
        The plain text content of the craft
        
    Raises:
        CraftContentError: If the craft content is missing or malformed
        
        The following exceptions may be raised by the API client:
        CraftNotFoundError: If the craft with the given ID is not found
        CraftAccessError: If access to the craft is denied (401/403)
        ValueError: If craft_id is empty or invalid
        httpx.HTTPStatusError: For other HTTP errors from the API
        httpx.RequestError: If a network error occurs
    """
    response = api_client.get_craft(craft_id)
    
    if "content" in response and "plain" in response["content"]:
        content = response["content"]["plain"]
        if content:
            return content
        else:
            raise CraftContentError(f"Craft {craft_id} exists but has no content")
    else:
        available_keys = list(response.keys())
        raise CraftContentError(f"Craft {craft_id} found but content structure is unexpected. Available keys: {available_keys}")


def main():
    """Main entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

