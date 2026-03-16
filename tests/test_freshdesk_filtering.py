import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.services.freshdesk_service import FreshdeskService

@pytest.mark.asyncio
async def test_get_tickets_with_filters():
    with patch("os.getenv") as mock_os_getenv:
        mock_os_getenv.side_effect = lambda key: {
            "FRESHDESK_API_KEY": "test_key",
            "FRESHDESK_DOMAIN": "test.freshdesk.com"
        }.get(key)
        
        service = FreshdeskService()
    
    # Mock the AsyncClient.get method
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 1, "subject": "Test"}]
    mock_response.raise_for_status = lambda: None
    
    with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
        # Test 1: Only updated_since
        await service.get_tickets(updated_since="2024-01-01T00:00:00Z")
        mock_get.assert_called_with(
            "https://test.freshdesk.com/api/v2/tickets",
            headers=service.headers,
            params={"updated_since": "2024-01-01T00:00:00Z"}
        )
        
        # Test 2: Email filter
        await service.get_tickets(email="user@example.com")
        mock_get.assert_called_with(
            "https://test.freshdesk.com/api/v2/tickets",
            headers=service.headers,
            params={"email": "user@example.com"}
        )
        
        # Test 3: Company ID filter
        await service.get_tickets(company_id=123)
        mock_get.assert_called_with(
            "https://test.freshdesk.com/api/v2/tickets",
            headers=service.headers,
            params={"company_id": 123}
        )
        
        # Test 4: Combined filters
        await service.get_tickets(updated_since="2024-01-01T00:00:00Z", email="user@example.com", company_id=123)
        mock_get.assert_called_with(
            "https://test.freshdesk.com/api/v2/tickets",
            headers=service.headers,
            params={
                "updated_since": "2024-01-01T00:00:00Z",
                "email": "user@example.com",
                "company_id": 123
            }
        )

if __name__ == "__main__":
    pytest.main([__file__])
