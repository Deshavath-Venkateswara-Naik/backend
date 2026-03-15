from fastapi import APIRouter, HTTPException, Query
from app.services.freshdesk_service import freshdesk_service
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.get("/tickets")
async def get_freshdesk_tickets(hours: int = Query(24, ge=1, le=240)):
    """
    Endpoint to fetch Freshdesk tickets with time filtering.
    Defaults to last 24 hours.
    """
    try:
        # Calculate the timestamp for 'hours' ago in UTC
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        # Freshdesk expects YYYY-MM-DDTHH:MM:SSZ
        timestamp = since_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        tickets = await freshdesk_service.get_tickets(updated_since=timestamp)
        return {
            "hours": hours,
            "since": timestamp,
            "ticket_count": len(tickets),
            "tickets": tickets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

