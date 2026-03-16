import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app

client = TestClient(app)

def test_create_ticket_success():
    """Test successful ticket creation."""
    mock_ticket_data = {
        "id": 12345,
        "subject": "Test Ticket",
        "description": "This is a test ticket",
        "email": "test@example.com",
        "priority": 1,
        "status": 2
    }
    
    with patch("app.services.freshdesk_service.FreshdeskService.create_ticket") as mock_create:
        mock_create.return_value = mock_ticket_data
        
        payload = {
            "subject": "Test Ticket",
            "description": "This is a test ticket",
            "email": "test@example.com",
            "priority": 1,
            "status": 2,
            "category": "login_issues"
        }
        
        response = client.post("/tickets", json=payload)
        
        assert response.status_code == 201
        assert response.json()["id"] == 12345
        assert mock_create.called
        
        # Verify category was added to custom_fields
        # The schema might change how it passes data to create_ticket
        # In our implementation, we add cf_category to custom_fields
        call_args = mock_create.call_args[0][0]
        assert call_args["custom_fields"]["cf_category"] == "login_issues"

def test_create_ticket_failure():
    """Test ticket creation failure."""
    with patch("app.services.freshdesk_service.FreshdeskService.create_ticket") as mock_create:
        mock_create.side_effect = Exception("Freshdesk API Error")
        
        payload = {
            "subject": "Test Ticket",
            "description": "This is a test ticket",
            "email": "test@example.com"
        }
        
        response = client.post("/tickets", json=payload)
        
        assert response.status_code == 500
        assert "Freshdesk API Error" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__])
