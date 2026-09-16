from fastapi import APIRouter
from pydantic import BaseModel
import re


router = APIRouter(
    prefix="/conversation",
    tags=["Conversation"]
)


# Temporary in-memory session storage
sessions = {}


class ConversationRequest(BaseModel):
    session_id: str
    message: str


def get_next_question(lead):
    if not lead.get("name"):
        return "What's your name?"

    if not lead.get("email"):
        return "Nice to meet you! What's your email address?"

    if not lead.get("phone"):
        return "What's your phone number?"

    if not lead.get("vehicle_year"):
        return "What year is your vehicle?"

    if not lead.get("vehicle_make"):
        return "What's the make of your vehicle? For example, Toyota, Ford, or Honda."

    if not lead.get("vehicle_model"):
        return "What's the model of your vehicle?"

    if lead.get("current_insurance") is None:
        return "Do you currently have car insurance? Please answer yes or no."

    if lead.get("current_insurance") and not lead.get("policy_expiry"):
        return "When does your current insurance policy expire?"

    if not lead.get("coverage_type"):
        return "What type of coverage are you looking for? For example, Full Coverage or Liability."

    if not lead.get("urgency"):
        return "When would you like to purchase your insurance? For example, Today, This Week, or Later."

    return None


def process_message(lead, message):
    message = message.strip()

    if not lead.get("name"):
        lead["name"] = message
        return

    if not lead.get("email"):
        if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message):
            lead["email"] = message
        return

    if not lead.get("phone"):
        phone = re.sub(r"\D", "", message)

        if len(phone) >= 7:
            lead["phone"] = phone

        return

    if not lead.get("vehicle_year"):
        match = re.search(r"\b(19|20)\d{2}\b", message)

        if match:
            lead["vehicle_year"] = int(match.group())

        return

    if not lead.get("vehicle_make"):
        lead["vehicle_make"] = message
        return

    if not lead.get("vehicle_model"):
        lead["vehicle_model"] = message
        return

    if lead.get("current_insurance") is None:
        answer = message.lower()

        if answer in ["yes", "y", "yeah", "yep"]:
            lead["current_insurance"] = True

        elif answer in ["no", "n", "nope"]:
            lead["current_insurance"] = False

        return

    if lead.get("current_insurance") and not lead.get("policy_expiry"):
        lead["policy_expiry"] = message
        return

    if not lead.get("coverage_type"):
        lead["coverage_type"] = message
        return

    if not lead.get("urgency"):
        lead["urgency"] = message
        return


@router.post("/message")
def send_message(request: ConversationRequest):

    if request.session_id not in sessions:
        sessions[request.session_id] = {
            "name": None,
            "email": None,
            "phone": None,
            "vehicle_year": None,
            "vehicle_make": None,
            "vehicle_model": None,
            "current_insurance": None,
            "policy_expiry": None,
            "coverage_type": None,
            "urgency": None
        }

    lead = sessions[request.session_id]

    process_message(lead, request.message)

    next_question = get_next_question(lead)

    if next_question:
        reply = next_question
        status = "collecting_information"
    else:
        reply = (
            "Perfect! I have all the information I need. "
            "Your insurance request is ready to be processed."
        )
        status = "completed"

    return {
        "session_id": request.session_id,
        "reply": reply,
        "status": status,
        "lead": lead
    }