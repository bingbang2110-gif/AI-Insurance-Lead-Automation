from pydantic import BaseModel


class InsuranceLead(BaseModel):
    name: str
    email: str
    phone: str
    vehicle_year: int
    vehicle_make: str
    vehicle_model: str
    current_insurance: bool
    policy_expiry: str | None = None
    coverage_type: str
    urgency: str


class Conversation(BaseModel):
    session_id: str
    current_step: str = "name"
    lead: dict = {}