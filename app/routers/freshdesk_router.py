from fastapi import APIRouter, HTTPException, Query, status
from app.services.freshdesk_service import freshdesk_service
from app.schemas.ticket_schema import TicketCreate, TicketStatusUpdate
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.get("/tickets")
async def get_freshdesk_tickets(
    hours: int = Query(24, ge=1, le=240),
    email: str | None = Query(None),
    company_id: int | None = Query(None)
):
    """
    Endpoint to fetch Freshdesk tickets with time filtering.
    Defaults to last 24 hours.
    """
    try:
        # Calculate the timestamp for 'hours' ago in UTC
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        # Freshdesk expects YYYY-MM-DDTHH:MM:SSZ
        timestamp = since_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        tickets = await freshdesk_service.get_tickets(
            updated_since=timestamp,
            email=email,
            company_id=company_id
        )
        return {
            "hours": hours,
            "email": email,
            "company_id": company_id,
            "since": timestamp,
            "ticket_count": len(tickets),
            "tickets": tickets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tickets", status_code=status.HTTP_201_CREATED)
async def create_freshdesk_ticket(ticket: TicketCreate):
    """
    Endpoint to create a new ticket in Freshdesk.
    """
    try:
        # Prepare the payload for Freshdesk
        ticket_data = {
            "subject": ticket.subject,
            "description": ticket.description,
            "email": ticket.email,
            "priority": ticket.priority,
            "status": ticket.status,
            "name": ticket.name,
            "phone": ticket.phone,
        }
        
        # Add custom fields if provided
        if ticket.custom_fields:
            ticket_data["custom_fields"] = ticket.custom_fields
            
        # If category is provided and it's not already in custom_fields, add it
        # Note: Freshdesk often uses custom fields for categories. 
        # For now, we'll just pass it through if it's explicitly set.
        if ticket.category:
            if "custom_fields" not in ticket_data:
                ticket_data["custom_fields"] = {}
            ticket_data["custom_fields"]["cf_category"] = ticket.category
            
        result = await freshdesk_service.create_ticket(ticket_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tickets/{ticket_id}/status")
async def update_freshdesk_ticket_status(ticket_id: int, update: TicketStatusUpdate):
    """
    Endpoint to update the status of an existing ticket in Freshdesk.
    """
    try:
        ticket_data = {"status": update.status}
        result = await freshdesk_service.update_ticket(ticket_id, ticket_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

