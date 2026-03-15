from openai import OpenAI
import os
from dotenv import load_dotenv
from app.utils.categories import ALLOWED_CATEGORIES

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_ticket_fields(message, validate=True):
    categories_str = "\n".join(f"  - {cat}" for cat in ALLOWED_CATEGORIES)

    validation_block = """
STEP 1 — VALIDATE:
Decide if this message should generate a ticket.

Generate a ticket (is_valid_ticket: true) if ANY of the following are true:
- The message describes a problem, complaint, question, or request — even if vague or short
- The message contains personal details (name, email, phone number) — even with a vague issue
- The message appears to be a real user describing something related to a product or service
- It is a chat/support conversation excerpt

Reject (is_valid_ticket: false) ONLY when the message is clearly not support-related AND contains no personal details — for example: a lone city/country name with nothing else, pure keyboard mashing, a single emoji, or completely unrelated content with zero support context.
When in doubt, accept and generate a ticket. It is always better to generate a ticket with missing fields than to reject a valid one.

If NOT valid, return ONLY:
{
  "is_valid_ticket": false,
  "reason": "One short sentence explaining why."
}

""" if validate else ""

    step_number = "STEP 2" if validate else "STEP 1"

    prompt = f"""
You are a support ticket extraction assistant for Turito, an educational platform.
{validation_block}
{step_number} — EXTRACT{"(only when valid)" if validate else ""}:
Extract one ticket per distinct issue. The text may come from OCR of handwritten notes or screenshots — spelling may be imperfect, interpret intelligently.

Fields:
- name: customer's full name (null if not found)
- email: customer's email address (null if not found)
- phone: customer's phone number (null if not found)
- issue: A professional, complete description of the problem. Do NOT copy the input verbatim — rewrite it as a clear support issue summary. Expand abbreviations, fix grammar, add context. Must be a full sentence or more.
- category: MUST be exactly one of the allowed categories below

ALLOWED CATEGORIES:
{categories_str}

RULES:
- "category" must be exactly one value from the allowed list.
- "issue" must be a complete, professional sentence — never a raw single word copy.
- Null out fields that are not present in the message.
- If multiple distinct issues exist, create one ticket per issue.

Return ONLY valid JSON:
{{
  "is_valid_ticket": true,
  "tickets": [
    {{
      "name": "...",
      "email": "...",
      "phone": "...",
      "issue": "...",
      "category": "..."
    }}
  ]
}}

Message:
{message}
"""
    
    print("\n--- [BACKEND] Extracting Ticket Fields ---")
    print(f"Prompt length: {len(prompt)} characters")
    print(f"Extracting from message: {message[:100]}...")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that extracts ticket information into JSON format."},
            {"role": "user", "content": prompt}
        ]
    )

    result = response.choices[0].message.content
    print("LLM Response received.")
    print(f"Raw Output: {result}")
    print("--- [BACKEND] Extraction Complete ---\n")
    return result


def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe an audio file using OpenAI Whisper API."""
    print(f"\n--- [BACKEND] Transcribing Audio: {audio_file_path} ---")
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        print(f"Transcription result: {transcript.text[:100]}...")
        print("--- [BACKEND] Transcription Complete ---\n")
        return transcript.text
    except Exception as e:
        print(f"Transcription error: {e}")
        raise e