import httpx
import os
import base64
from dotenv import load_dotenv
from app.services.llm_service import categorize_freshdesk_tickets

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

    async def get_tickets(self, updated_since: str | None = None, email: str | None = None, company_id: int | None = None):
        """
        Fetch tickets from Freshdesk.
        :param updated_since: ISO 8601 timestamp (YYYY-MM-DDTHH:MM:SSZ)
        :param email: Filter by requester email
        :param company_id: Filter by company ID
        """
        url = f"{self.base_url}/tickets"
        params = {}
        if updated_since:
            params["updated_since"] = updated_since
        if email:
            params["email"] = email
        if company_id:
            params["company_id"] = company_id
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                tickets = response.json()
                
                # Perform AI categorization
                if tickets and isinstance(tickets, list):
                    ai_mapping = categorize_freshdesk_tickets(tickets)
                    for ticket in tickets:
                        ticket_id = str(ticket.get("id"))
                        ticket["ai_category"] = ai_mapping.get(ticket_id, "platform_tech_issue")
                
                return tickets
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Failed to fetch tickets: {e.response.text}")
            except Exception as e:
                print(f"An error occurred: {e}")
                raise e

    async def create_ticket(self, ticket_data: dict):
        """
        Create a ticket in Freshdesk.
        :param ticket_data: Dictionary containing ticket fields
        """
        url = f"{self.base_url}/tickets"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=self.headers, json=ticket_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Failed to create ticket: {e.response.text}")
            except Exception as e:
                print(f"An error occurred: {e}")
                raise e

    async def update_ticket(self, ticket_id: int, ticket_data: dict):
        """
        Update a ticket in Freshdesk.
        :param ticket_id: ID of the ticket to update
        :param ticket_data: Dictionary containing fields to update
        """
        url = f"{self.base_url}/tickets/{ticket_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(url, headers=self.headers, json=ticket_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Failed to update ticket: {e.response.text}")
            except Exception as e:
                print(f"An error occurred: {e}")
                raise e

freshdesk_service = FreshdeskService()

