import base64
import os
import io
from openai import OpenAI
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_image(image_bytes: bytes) -> str:
    """Send image to GPT-4o for OCR and return the extracted text."""
    # Encode image to base64
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    print("\n--- [BACKEND] Extracting Text with GPT-4o Vision ---")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all the text from this image. Return just the text content, preserving the layout as much as possible with newlines."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )

        extracted_text = response.choices[0].message.content
        print("GPT-4o OCR Complete.")
        return extracted_text.strip()
    except Exception as e:
        print(f"GPT-4o OCR Error: {e}")
        return ""


def split_into_tickets(text: str) -> list[str]:
    """Split OCR text into individual ticket blocks.

    Heuristics:
    - Split on blank-line-separated blocks (double newline).
    - If only one block, treat the whole text as a single ticket.
    - Filter out very short noise fragments (< 15 chars).
    """
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    # Filter noise
    blocks = [b for b in blocks if len(b) >= 15]
    if not blocks:
        return [text.strip()] if text.strip() else []
    return blocks
