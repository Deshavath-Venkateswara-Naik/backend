import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pytest

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app

client = TestClient(app)

def test_update_ticket_status_success():
    """Test successful ticket status update."""
    mock_response_data = {
        "id": 12345,
        "status": 5,
        "subject": "Test Ticket"
    }
    
    with patch("app.services.freshdesk_service.FreshdeskService.update_ticket") as mock_update:
        mock_update.return_value = mock_response_data
        
        payload = {"status": 5}
        response = client.put("/tickets/12345/status", json=payload)
        
        assert response.status_code == 200
        assert response.json()["status"] == 5
        assert mock_update.called
        assert mock_update.call_args[0][0] == 12345
        assert mock_update.call_args[0][1] == {"status": 5}

def test_update_ticket_status_failure():
    """Test ticket status update failure."""
    with patch("app.services.freshdesk_service.FreshdeskService.update_ticket") as mock_update:
        mock_update.side_effect = Exception("Freshdesk API Error")
        
        payload = {"status": 4}
        response = client.put("/tickets/12345/status", json=payload)
        
        assert response.status_code == 500
        assert "Freshdesk API Error" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__])
