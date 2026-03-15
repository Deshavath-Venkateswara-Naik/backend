from pydantic import BaseModel

class MessageInput(BaseModel):
    message: str

class TicketResponse(BaseModel):
    name: str | None
    email: str | None
    phone: str | None
    issue: str | None
    category: str | None