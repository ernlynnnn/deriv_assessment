import json
from pathlib import Path
from datetime import datetime


REQUIRED_FIELDS = {
    "ticket_id": str,
    "channel": str,
    "customer_tier": str,
    "language_hint": str,
    "subject": str,
    "message": str,
    "created_at": str,
}


def validate_ticket(ticket):
    """Validate a single ticket's structure and fields."""

    if not isinstance(ticket, dict):
        raise ValueError("Each ticket must be a JSON object.")

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in ticket:
            raise ValueError(f"Missing required field: {field}")

        if not isinstance(ticket[field], expected_type):
            raise ValueError(
                f"Field '{field}' must be {expected_type.__name__}"
            )

    if not ticket["ticket_id"].strip():
        raise ValueError("Ticket ID cannot be empty.")

    if not ticket["subject"].strip() and not ticket["message"].strip():
        raise ValueError("Ticket must contain a subject or message.")

    try:
        datetime.fromisoformat(
            ticket["created_at"].replace("Z", "+00:00")
        )
    except ValueError:
        raise ValueError("Invalid created_at timestamp.")

    return ticket


def load_tickets(file_path):
    """Load and validate tickets from a JSON file."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        tickets = json.load(file)

    if not isinstance(tickets, list):
        raise ValueError("tickets.json must contain a JSON array.")

    validated_tickets = []
    seen_ids = set()

    for ticket in tickets:
        validated = validate_ticket(ticket)
        ticket_id = validated["ticket_id"]

        if ticket_id in seen_ids:
            raise ValueError(f"Duplicate ticket ID: {ticket_id}")

        seen_ids.add(ticket_id)
        validated_tickets.append(validated)

    return validated_tickets


def save_tickets(tickets, output_path):
    """Save ingested tickets as an intermediate artifact."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            tickets,
            file,
            ensure_ascii=False,
            indent=2
        )


def run_ingestion(input_path, output_path):
    """Execute the ticket ingestion stage."""

    tickets = load_tickets(input_path)
    save_tickets(tickets, output_path)

    print("Stage: TICKETS_LOADED")
    print(f"Successfully loaded {len(tickets)} tickets.")
    print(f"Output saved to: {output_path}")

    return tickets


if __name__ == "__main__":
    run_ingestion(
        input_path="tickets.json",
        output_path="runs/run_001/preprocessed_tickets.json"
    )
