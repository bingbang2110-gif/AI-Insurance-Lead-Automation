import os
import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from app.database.database import SessionLocal
from app.database.models import Lead

from app.services.scoring import (
    calculate_lead_score,
    calculate_priority,
)
from app.agents.insurance_agent import extract_lead_information

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


class ChatRequest(BaseModel):
    session_id: str
    message: str

def update_lead_from_ai(lead: Lead, message: str):
    """
    Extract structured lead information using AI
    and update only the fields explicitly provided.
    """

    data = extract_lead_information(message)

    # Normalize urgency values
    urgency = data.get("urgency")

    if urgency == "immediate":
        urgency = "immediately"

    # Fallback: detect urgency directly from the message
    if not urgency:
        lower_message = message.lower().strip()

        if any(phrase in lower_message for phrase in [
            "immediately",
            "immediate",
            "right now",
            "today",
            "asap",
            "as soon as possible",
            "urgent"
        ]):
            urgency = "immediately"

        elif any(phrase in lower_message for phrase in [
            "within a week",
            "this week",
            "next week"
        ]):
            urgency = "within a week"

    if urgency:
        data["urgency"] = urgency

    for field, value in data.items():
        if value is not None:
            setattr(lead, field, value)

def get_next_question(lead: Lead):
    """
    Determine the next missing piece of information.
    """

    if not lead.name:
        return "What's your name?"

    if not lead.email:
        return "What's your email?"

    if not lead.phone:
        return "What's your phone number?"

    if lead.vehicle_year is None:
        return "What year is your vehicle?"

    if not lead.vehicle_make:
        return "What is the make of your vehicle?"

    if not lead.vehicle_model:
        return "What is the model of your vehicle?"

    if lead.current_insurance is None:
        return "Do you currently have car insurance?"

    if not lead.coverage_type:
        return "What type of coverage are you looking for?"

    if not lead.policy_expiry:
        return "When does your current policy expire?"

    if not lead.urgency:
        return "How soon do you need the insurance?"

    return None


def update_lead_from_message(
    lead: Lead,
    message: str
):
    """
    Save the user's message into the next missing Lead field.
    """

    message = message.strip()

    if not message:
        return

    # -------------------------
    # Name
    # -------------------------
    if not lead.name:

        insurance_words = [
            "insurance",
            "car insurance",
            "auto insurance",
            "quote",
            "coverage",
            "need insurance",
        ]

        if not any(
            word in message.lower()
            for word in insurance_words
        ):
            lead.name = message

        return

    # -------------------------
    # -------------------------
    # Email
    # -------------------------
    if not lead.email:

        lower_message = message.lower().strip()

        if (
            "@" in lower_message
            and "." in lower_message.split("@")[-1]
            and " " not in lower_message
        ):
            lead.email = message

        return

    # -------------------------
    # -------------------------
    # Phone
    # -------------------------
    if not lead.phone:

        cleaned_phone = (
            message
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        if cleaned_phone.startswith("+"):
            phone_digits = cleaned_phone[1:]
        else:
            phone_digits = cleaned_phone

        if (
            phone_digits.isdigit()
            and 7 <= len(phone_digits) <= 15
        ):
            lead.phone = message

        return

    # -------------------------
    # -------------------------
    # Vehicle year
    # -------------------------
    if lead.vehicle_year is None:

        cleaned_year = message.strip()

        if (
            cleaned_year.isdigit()
            and len(cleaned_year) == 4
            and 1900 <= int(cleaned_year) <= 2030
        ):
            lead.vehicle_year = int(cleaned_year)

        return

    # -------------------------
    # Vehicle make
    # -------------------------
    if not lead.vehicle_make:

        lead.vehicle_make = message

        return

    # -------------------------
    # Vehicle model
    # -------------------------
    if not lead.vehicle_model:

        lead.vehicle_model = message

        return

    # -------------------------
    # -------------------------
       # -------------------------
    # Current insurance
    # -------------------------
    if lead.current_insurance is None:

        lower_message = message.lower().strip()

        yes_answers = [
            "yes",
            "y",
            "yeah",
            "yep",
            "sure",
            "yes i do",
            "yes i have",
            "i do",
            "i have insurance",
            "i am insured",
            "currently insured",
        ]

        no_answers = [
            "no",
            "n",
            "nope",
            "nah",
            "no i don't",
            "no i do not",
            "no i have not",
            "i don't",
            "i do not",
            "i don't have insurance",
            "not insured",
        ]

        if lower_message in yes_answers:
            lead.current_insurance = True

        elif lower_message in no_answers:
            lead.current_insurance = False

        else:
            return

        return

    # -------------------------
    # Coverage type
    # -------------------------
    if not lead.coverage_type:

        lower_message = message.lower().strip()

        if (
            "full coverage" in lower_message
            or lower_message == "full"
            or "i want full coverage" in lower_message
            or "full insurance" in lower_message
        ):
            lead.coverage_type = "Full coverage"

        elif (
            "third-party" in lower_message
            or "third party" in lower_message
            or lower_message == "third"
            or "third party insurance" in lower_message
        ):
            lead.coverage_type = "Third-party"

        else:
            lead.coverage_type = message

        return

    # -------------------------
  # -------------------------
    # Policy expiry
    # -------------------------
    if not lead.policy_expiry:

        import re
        from datetime import datetime

        lower_message = message.lower().strip()

        valid_date = False

        date_formats = [
            "%B %d, %Y",
            "%b %d, %Y",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m-%d",
        ]

        for date_format in date_formats:
            try:
                datetime.strptime(message.strip(), date_format)
                valid_date = True
                break
            except ValueError:
                pass

        # Reject obvious non-date values
        if not valid_date:
            lead.policy_expiry = None
            return

        lead.policy_expiry = message.strip()

        return

    # -------------------------
    # -------------------------
    # Urgency
    # -------------------------
    if not lead.urgency:

        lower_message = message.lower().strip()

        if (
            "immediately" in lower_message
            or "right now" in lower_message
            or "today" in lower_message
            or "asap" in lower_message
            or "as soon as possible" in lower_message
            or "urgent" in lower_message
        ):
            lead.urgency = "Immediately"

        elif (
            "within a week" in lower_message
            or "this week" in lower_message
            or "next week" in lower_message
        ):
            lead.urgency = "Within a week"

        elif (
            "within a month" in lower_message
            or "this month" in lower_message
            or "next month" in lower_message
        ):
            lead.urgency = "Within a month"

        else:
            lead.urgency = message

        return

def generate_lead_summary(lead: Lead):
    """
    Generate a simple human-readable summary.
    """

    name = lead.name or "The customer"

    if lead.current_insurance is True:
        insurance_status = "currently insured"

    elif lead.current_insurance is False:
        insurance_status = "not currently insured"

    else:
        insurance_status = "insurance status is unknown"

    vehicle_parts = []

    if lead.vehicle_year:
        vehicle_parts.append(str(lead.vehicle_year))

    if lead.vehicle_make:
        vehicle_parts.append(lead.vehicle_make)

    if lead.vehicle_model:
        vehicle_parts.append(lead.vehicle_model)

    vehicle = (
        " ".join(vehicle_parts)
        if vehicle_parts
        else "vehicle"
    )

    coverage = (
        lead.coverage_type
        or "car insurance"
    )

    summary = (
        f"{name} is looking for "
        f"{coverage} for a {vehicle}. "
        f"The customer is {insurance_status}"
    )

    if lead.policy_expiry:
        summary += (
            f" and their current policy expires "
            f"on {lead.policy_expiry}."
        )

    else:
        summary += "."

    if lead.urgency:
        summary += (
            f" Insurance is needed "
            f"{lead.urgency.lower()}."
        )

    return summary


@router.post("/")
def chat(request: ChatRequest):

    db = SessionLocal()

    try:

        # -------------------------
        # Find existing Lead
        # -------------------------
        lead = (
            db.query(Lead)
            .filter(
                Lead.session_id == request.session_id
            )
            .first()
        )

        # -------------------------
        # Create new Lead
        # -------------------------
        if not lead:

            lead = Lead(
                session_id=request.session_id
            )

            db.add(lead)
            db.commit()
            db.refresh(lead)

        # -------------------------
        # Save user's answer
        # -------------------------
        # Check whether lead was already complete
        was_complete = get_next_question(lead) is None
        update_lead_from_ai(
            lead,
            request.message
        )

        # -------------------------
        # Calculate score
        # -------------------------
        lead.lead_score = calculate_lead_score(
            lead
        )

        # -------------------------
        # Calculate priority
        # -------------------------
        lead.priority = calculate_priority(
            lead.lead_score
        )

        # -------------------------
        # Check next question
        # -------------------------
        next_question = get_next_question(
            lead
        )

        if next_question:

            status = "collecting_information"
            reply = next_question

        else:

            # -------------------------
            # Lead is complete
            # -------------------------
            lead.summary = generate_lead_summary(
                lead
            )

            status = "completed"

            reply = (
                "Thanks! I have all the information "
                "I need. Your insurance lead has been "
                "submitted successfully."
            )

        # -------------------------
        # Save changes
        # -------------------------
        db.commit()
        db.refresh(lead)
        # -------------------------
        # Send completed lead to n8n
        # -------------------------
        if status == "completed" and not was_complete:

            n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")

            if n8n_webhook_url:
                payload = {
                    "event": "lead.completed",
                    "lead_id": lead.id,
                    "name": lead.name,
                    "email": lead.email,
                    "phone": lead.phone,
                    "priority": lead.priority,
                    "lead_score": lead.lead_score,
                    "coverage_type": lead.coverage_type,
                    "urgency": lead.urgency,
                    "summary": lead.summary,
                }

                try:
                    response = httpx.post(
                        n8n_webhook_url,
                        json=payload,
                        timeout=5.0
                    )
                    response.raise_for_status()
                    print("n8n completion webhook sent successfully")

                except httpx.HTTPError as e:
                    print("n8n webhook error:", e)

        return {
            "session_id": request.session_id,
            "reply": reply,
            "status": status,
            "lead": lead
        }

        return {
            "session_id": request.session_id,
            "reply": reply,
            "status": status,
            "lead": lead
        }

    finally:

        db.close()
