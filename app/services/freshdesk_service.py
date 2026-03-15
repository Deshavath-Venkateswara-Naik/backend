import httpx
import os
import base64
from dotenv import load_dotenv

load_dotenv()

class FreshdeskService:
    def __init__(self):
        self.api_key = os.getenv("FRESHDESK_API_KEY")
        self.domain = os.getenv("FRESHDESK_DOMAIN")
        self.base_url = f"https://{self.domain}/api/v2"
        
        # Prepare Basic Auth header
        auth_str = f"{self.api_key}:X"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }

    async def get_tickets(self, updated_since: str | None = None):
        """
        Fetch tickets from Freshdesk.
        :param updated_since: ISO 8601 timestamp (YYYY-MM-DDTHH:MM:SSZ)
        """
        url = f"{self.base_url}/tickets"
        params = {}
        if updated_since:
            params["updated_since"] = updated_since
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Failed to fetch tickets: {e.response.text}")
            except Exception as e:
                print(f"An error occurred: {e}")
                raise e

freshdesk_service = FreshdeskService()

