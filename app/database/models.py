from sqlalchemy import Column, Integer, String, Boolean
from app.database.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=True)

    name = Column(String)
    email = Column(String)
    phone = Column(String)

    vehicle_year = Column(Integer)
    vehicle_make = Column(String)
    vehicle_model = Column(String)

    current_insurance = Column(Boolean)
    policy_expiry = Column(String)

    coverage_type = Column(String)
    urgency = Column(String)

    lead_score = Column(Integer)
    priority = Column(String)
    summary = Column(String)