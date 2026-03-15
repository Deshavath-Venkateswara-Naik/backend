from fastapi import APIRouter, UploadFile, File
from app.schemas.ticket_schema import MessageInput
from app.services.llm_service import extract_ticket_fields, transcribe_audio
from app.services.ocr_service import extract_text_from_image, split_into_tickets
from app.utils.categories import ALLOWED_CATEGORIES
import json
import re
import difflib
import os
import uuid
import shutil

router = APIRouter()


def _strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences (```json ... ```) from LLM output."""
    text = text.strip()
    # Remove opening fence like ```json or ```
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    # Remove closing fence
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _validate_category(category: str | None) -> str:
    """Ensure the category is one of the allowed values.
    Falls back to fuzzy matching, then to 'platform_tech_issue'."""
    if not category:
        return "platform_tech_issue"

    normalized = category.strip().lower().replace(" ", "_").replace("-", "_")

    if normalized in ALLOWED_CATEGORIES:
        return normalized

    # Fuzzy match – pick the closest allowed category
    matches = difflib.get_close_matches(normalized, ALLOWED_CATEGORIES, n=1, cutoff=0.4)
    if matches:
        return matches[0]

    return "platform_tech_issue"


def _process_ticket_text(text: str, validate=True) -> list[dict] | dict:
    """Run LLM extraction on a single ticket text and validate the category for each result.
    Returns a list of ticket dicts on success, or a dict with _not_a_ticket=True on invalid input.
    Set validate=False for image OCR to skip the is_valid_ticket check."""
    raw = extract_ticket_fields(text, validate=validate)
    cleaned = _strip_markdown_fences(raw)
    try:
        data = json.loads(cleaned)

        # Handle invalid input signal from LLM
        if not data.get("is_valid_ticket", True):
            return {
                "_not_a_ticket": True,
                "reason": data.get("reason", "This doesn't appear to be a valid support request.")
            }

        tickets = data.get("tickets", [])
        if not isinstance(tickets, list):
            tickets = [data] if data else []

        for ticket in tickets:
            ticket["category"] = _validate_category(ticket.get("category"))
            # Tag which fields are missing so the frontend can highlight them
            ticket["_missing_fields"] = [
                f for f in ["name", "email", "phone", "issue"]
                if not ticket.get(f)
            ]
        return tickets
    except Exception as e:
        print(f"Error parsing LLM JSON: {e}")
        raise e


@router.post("/generate-ticket")
def generate_ticket(data: MessageInput):
    """Generate one or more tickets from a text/voice message."""
    result = _process_ticket_text(data.message)

    # Propagate invalid-input signal to the frontend
    if isinstance(result, dict) and result.get("_not_a_ticket"):
        return result

    tickets = result
    if not tickets:
        return {
            "_not_a_ticket": True,
            "reason": "Could not extract ticket information from this message. Please provide more details."
        }
    return {"tickets": tickets}


@router.post("/generate-tickets-from-image")
async def generate_tickets_from_image(file: UploadFile = File(...)):
    """Accept an image upload, run OCR, split into tickets, extract fields."""
    image_bytes = await file.read()

    # Step 1: OCR
    ocr_text = extract_text_from_image(image_bytes)

    # Step 2: Only reject if OCR found absolutely no text (blank/pure photo with no text at all)
    if not ocr_text or not ocr_text.strip():
        return {
            "ocr_text": ocr_text,
            "ticket_count": 0,
            "tickets": [{"_not_a_ticket": True, "reason": "No readable text found in this image. Please upload a screenshot or photo containing text."}],
        }

    # Step 3: Split into individual ticket blocks
    ticket_blocks = split_into_tickets(ocr_text)

    # Step 4: Extract fields from each block via the LLM (no validation — OCR text is trusted if it exists)
    tickets = []
    for block in ticket_blocks:
        try:
            result = _process_ticket_text(block, validate=False)
            if isinstance(result, dict) and result.get("_not_a_ticket"):
                tickets.append({**result, "_source_text": block})
                continue
            for ticket in result:
                ticket["_source_text"] = block
                tickets.append(ticket)
        except Exception:
            tickets.append({
                "name": None,
                "email": None,
                "phone": None,
                "issue": block,
                "category": "platform_tech_issue",
                "_source_text": block,
                "_error": "Failed to parse this ticket block",
            })

    return {
        "ocr_text": ocr_text,
        "ticket_count": len(tickets),
        "tickets": tickets,
    }


@router.get("/categories")
def get_categories():
    return {"categories": ALLOWED_CATEGORIES}


@router.post("/generate-ticket-audio")
async def generate_ticket_audio(file: UploadFile = File(...)):
    """Transcribe audio file then extract ticket fields."""
    print(f"\n--- [ROUTER] POST /generate-ticket-audio received ---")
    print(f"Incoming file: {file.filename}, Content-Type: {file.content_type}")

    temp_dir = "temp_audio"
    os.makedirs(temp_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1] or ".webm"
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}{file_ext}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        transcript = transcribe_audio(temp_file_path)
        result = _process_ticket_text(transcript)
        if isinstance(result, dict) and result.get("_not_a_ticket"):
            result["_transcript"] = transcript
            ticket_data = result
        else:
            ticket_data = result[0] if result else {
                "_not_a_ticket": True,
                "reason": "Could not extract ticket information from this audio.",
            }
            ticket_data["_transcript"] = transcript

        print(f"Success: Ticket generated from audio.")
        return ticket_data

    except Exception as e:
        print(f"Error in generate_ticket_audio: {e}")
        return {"error": str(e)}
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Cleaned up temp file: {temp_file_path}")