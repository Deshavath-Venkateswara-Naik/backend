from pydantic import BaseModel

class MessageInput(BaseModel):
    message: str

class TicketResponse(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    issue: str | None
    category: str | None

class TicketCreate(BaseModel):
    subject: str
    description: str
    email: str
    priority: int = 1
    status: int = 2
    name: str | None = None
    phone: str | None = None
    category: str | None = None
    custom_fields: dict | None = None

class TicketStatusUpdate(BaseModel):
    status: int