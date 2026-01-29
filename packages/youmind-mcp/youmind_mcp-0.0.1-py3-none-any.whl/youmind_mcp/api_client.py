import os
import httpx
from typing import Dict, Any
from dotenv import load_dotenv
from .exceptions import CraftNotFoundError, CraftAccessError

load_dotenv()


class YouMindAPIClient:
    def __init__(self):
        self.base_url = "https://youmind.com/api/v1"
        self.auth_token = os.getenv("YOUMIND_AUTH_TOKEN")
        if not self.auth_token:
            raise ValueError("YOUMIND_AUTH_TOKEN environment variable is not set")
        
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "cookie": self.auth_token,
            "origin": "https://youmind.com",
            "pragma": "no-cache",
            "referer": "https://youmind.com/",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "x-client-type": "web",
            "x-time-zone": "Asia/Shanghai",
            "x-use-snake-case": "true",
        }
    
    def get_craft(self, craft_id: str) -> Dict[str, Any]:
        """
        Retrieve craft content by craft ID.
        
        Args:
            craft_id: The ID of the craft to retrieve
            
        Returns:
            The full API response as a dictionary
            
        Raises:
            CraftNotFoundError: If the craft with the given ID is not found (404)
            CraftAccessError: If access to the craft is denied (401/403)
            ValueError: If craft_id is empty
            httpx.HTTPStatusError: For other HTTP errors
            httpx.RequestError: If a network error occurs
        """
        if not craft_id:
            raise ValueError("craft_id cannot be empty")
        
        url = f"{self.base_url}/getCraft"
        payload = {"id": craft_id}
        
        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise CraftNotFoundError(f"Craft with ID '{craft_id}' not found") from e
            elif e.response.status_code == 401:
                raise CraftAccessError("Authentication failed. Please check your YOUMIND_AUTH_TOKEN") from e
            elif e.response.status_code == 403:
                raise CraftAccessError(f"Access forbidden for craft '{craft_id}'. You may not have permission to view this craft") from e
            else:
                raise

