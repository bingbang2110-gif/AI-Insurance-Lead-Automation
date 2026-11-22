from typing import Annotated
from fastapi import APIRouter, HTTPException
import httpx
import os
from datetime import date
from pydantic import BaseModel, Field, EmailStr, ConfigDict, StringConstraints

from app.database.database import SessionLocal
from app.database.models import Lead
from app.services.scoring import calculate_lead_score, calculate_priority

class LeadCreate(BaseModel):
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    email: EmailStr
    phone: str = Field(
        min_length=7,
        max_length=20,
        pattern=r"^\+?[0-9\s()-]+$"
)
    vehicle_year: int | None = Field(default=None, ge=1886, le=2026)
    vehicle_make: str | None = None
    vehicle_model: str | None = None
    current_insurance: bool | None = None
    coverage_type: str | None = Field(
    default=None,
    pattern=r"^(life|health|auto|home|travel)$"
)
    policy_expiry: date | None = None
    urgency: str | None = Field(
    default=None,
    pattern=r"^(immediately|high|today|within a week)$"
)
    priority: str | None = None


class LeadUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=20,
        pattern=r"^\+?[0-9\s()-]+$"
    )

    vehicle_year: int | None = Field(
        default=None,
        ge=1886,
        le=2026
    )
    vehicle_make: str | None = None
    vehicle_model: str | None = None

    current_insurance: bool | None = None
    policy_expiry: date | None = None

    coverage_type: str | None = Field(
        default=None,
        pattern=r"^(life|health|auto|home|travel)$"
    )
    urgency: str | None = Field(
        default=None,
        pattern=r"^(immediately|high|today|within a week)$"
    )

    

router = APIRouter(
    prefix="/leads",
    tags=["Leads"]
)

def generate_lead_summary(lead):
    name = lead.name or "The customer"

    vehicle_parts = []

    if lead.vehicle_year:
        vehicle_parts.append(str(lead.vehicle_year))

    if lead.vehicle_make:
        vehicle_parts.append(lead.vehicle_make)

    if lead.vehicle_model:
        vehicle_parts.append(lead.vehicle_model)

    vehicle = " ".join(vehicle_parts) if vehicle_parts else "vehicle"

    coverage = lead.coverage_type or "insurance coverage"

    if lead.current_insurance is True:
        insurance_sentence = "The customer is currently insured."
    elif lead.current_insurance is False:
        insurance_sentence = "The customer is not currently insured."
    else:
        insurance_sentence = "The customer's insurance status is unknown."

    if lead.policy_expiry:
        expiry_sentence = (
            f"Their current policy expires on {lead.policy_expiry}."
        )
    else:
        expiry_sentence = "Their policy expiry date is unknown."

    if lead.urgency:
        urgency_sentence = (
            f"Insurance is needed {lead.urgency.lower()}."
        )
    else:
        urgency_sentence = ""

    return (
        f"{name} is looking for {coverage} for a {vehicle}. "
        f"{insurance_sentence} "
        f"{expiry_sentence} "
        f"{urgency_sentence}"
    )


@router.get("/")

def get_leads():
    db = SessionLocal()

    try:
        leads = db.query(Lead).all()
        return leads

    finally:
        db.close()


@router.post("/")
def create_lead(lead_data: LeadCreate):
    db = SessionLocal()

    try:
        lead = Lead(
            name=lead_data.name,
            email=lead_data.email,
            phone=lead_data.phone,
            vehicle_year=lead_data.vehicle_year,
            vehicle_make=lead_data.vehicle_make,
            vehicle_model=lead_data.vehicle_model,
            current_insurance=lead_data.current_insurance,
            coverage_type=lead_data.coverage_type,
            policy_expiry=lead_data.policy_expiry,
            urgency=lead_data.urgency,
            #priority=lead_data.priority
        )

        score = calculate_lead_score(lead)

        print("CALCULATED SCORE:", score)

        lead.lead_score = score
        lead.priority = calculate_priority(lead.lead_score)
        lead.summary = generate_lead_summary(lead)

        db.add(lead)
        db.commit()
        db.refresh(lead)
        n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")

        if n8n_webhook_url:
            payload = {
                "event": "lead.created",
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
                print("n8n webhook sent successfully")
            except httpx.HTTPError as e:
                print("n8n webhook error:", e)


        return lead

    finally:
        db.close()


@router.get("/filter/search")
def filter_leads(
    search: str | None = None,
    priority: str | None = None,
    coverage_type: str | None = None,
    urgency: str | None = None,
    vehicle_make: str | None = None,
    current_insurance: bool | None = None,
    sort_by: str | None = None,
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 10
):
    db = SessionLocal()

    try:
        query = db.query(Lead)

        if search:
            search_pattern = f"%{search}%"

            query = query.filter(
                Lead.name.ilike(search_pattern)
                | Lead.phone.ilike(search_pattern)
                | Lead.email.ilike(search_pattern)
            )

        if priority:
            query = query.filter(
                Lead.priority.ilike(priority)
            )

        if coverage_type:
            query = query.filter(
                Lead.coverage_type.ilike(coverage_type)
            )

        if urgency:
            query = query.filter(
                Lead.urgency.ilike(urgency)
            )

        if vehicle_make:
            query = query.filter(
                Lead.vehicle_make.ilike(vehicle_make)
            )

        if current_insurance is not None:
            query = query.filter(
                Lead.current_insurance == current_insurance
            )

        if sort_by == "lead_score":
            if sort_order == "asc":
                query = query.order_by(
                    Lead.lead_score.asc()
                )
            else:
                query = query.order_by(
                    Lead.lead_score.desc()
                )

        total = query.count()

        offset = (page - 1) * limit

        leads = (
            query
            .offset(offset)
            .limit(limit)
            .all()
        )

        total_pages = (
            (total + limit - 1) // limit
            if limit > 0
            else 0
        )

        return {
            "count": len(leads),
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "leads": leads
        }

    finally:
        db.close()


@router.get("/stats/summary")
def get_lead_stats():
    db = SessionLocal()

    try:
        leads = db.query(Lead).all()

        total_leads = len(leads)

        high_priority = sum(
            1 for lead in leads
            if lead.priority == "high"
        )

        medium_priority = sum(
            1 for lead in leads
            if lead.priority == "medium"
        )

        low_priority = sum(
            1 for lead in leads
            if lead.priority == "low"
        )

        insured = sum(
            1 for lead in leads
            if lead.current_insurance is True
        )

        not_insured = sum(
            1 for lead in leads
            if lead.current_insurance is False
        )

        scores = [
            lead.lead_score
            for lead in leads
            if lead.lead_score is not None
        ]

        if scores:
            average_score = sum(scores) / len(scores)
        else:
            average_score = 0

        return {
            "total_leads": total_leads,
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "insured": insured,
            "not_insured": not_insured,
            "average_score": round(average_score, 2)
        }

    finally:
        db.close()


@router.get("/{lead_id}")
def get_lead(lead_id: int):
    db = SessionLocal()

    try:
        lead = (
            db.query(Lead)
            .filter(Lead.id == lead_id)
            .first()
        )

        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

        return lead

    finally:
        db.close()


@router.delete("/{lead_id}")
def delete_lead(lead_id: int):
    db = SessionLocal()

    try:
        lead = (
            db.query(Lead)
            .filter(Lead.id == lead_id)
            .first()
        )

        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

        db.delete(lead)
        db.commit()

        return {
            "message": "Lead deleted successfully",
            "lead_id": lead_id
        }

    finally:
        db.close()


@router.put("/{lead_id}")
def update_lead(
    lead_id: int,
    data: LeadUpdate
):
    db = SessionLocal()

    try:
        lead = (
            db.query(Lead)
            .filter(Lead.id == lead_id)
            .first()
        )

        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

        update_data = data.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(lead, field, value)

        # Recalculate lead score
        lead.lead_score = calculate_lead_score(lead)
        lead.summary = generate_lead_summary(lead)

        # Recalculate priority
        lead.priority = calculate_priority(lead.lead_score)
        
        db.commit()
        db.refresh(lead)
        n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")

        if n8n_webhook_url:
            payload = {
                "event": "lead.updated",
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
                print("n8n webhook sent successfully")
            except httpx.HTTPError as e:
                print("n8n webhook error:", e)

        return lead

    finally:
        db.close()
@router.get("/automation/leads/{lead_id}")
def get_automation_lead(lead_id: int):
    db = SessionLocal()

    try:
        lead = (
            db.query(Lead)
            .filter(Lead.id == lead_id)
            .first()
        )

        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

        if not lead.summary:
            raise HTTPException(
                status_code=400,
                detail="Lead is not completed yet"
            )

        return {
            "event": "lead.completed",
            "lead_id": lead.id,
            "session_id": lead.session_id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "vehicle": {
                "year": lead.vehicle_year,
                "make": lead.vehicle_make,
                "model": lead.vehicle_model
            },
            "current_insurance": lead.current_insurance,
            "coverage_type": lead.coverage_type,
            "policy_expiry": lead.policy_expiry,
            "urgency": lead.urgency,
            "lead_score": lead.lead_score,
            "priority": lead.priority,
            "summary": lead.summary
        }

    finally:
        db.close()