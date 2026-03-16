import asyncio
import json
from app.services.llm_service import categorize_freshdesk_tickets

async def test_categorization():
    sample_tickets = [
        {
            "id": 12345,
            "subject": "Unable to login to my account",
            "description_text": "I keep getting an invalid password error even after resetting it."
        },
        {
            "id": 67890,
            "subject": "Refund request for last month",
            "description_text": "I was charged twice for my subscription and I want a refund."
        },
        {
            "id": 11223,
            "subject": "How to change my tutor?",
            "description_text": "I'm not happy with my current tutor and want to switch."
        }
    ]

    print("Testing categorization...")
    mapping = categorize_freshdesk_tickets(sample_tickets)
    print("Mapping result:")
    print(json.dumps(mapping, indent=2))

    # Check against allowed categories
    from app.utils.categories import ALLOWED_CATEGORIES
    for tid_str, cat in mapping.items():
        if cat not in ALLOWED_CATEGORIES:
            print(f"  WARNING: Category '{cat}' for ticket {tid_str} is not in ALLOWED_CATEGORIES!")
        else:
            print(f"  Ticket {tid_str} categorized as '{cat}' correctly.")

if __name__ == "__main__":
    asyncio.run(test_categorization())
