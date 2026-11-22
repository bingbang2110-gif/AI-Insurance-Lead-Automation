
from types import SimpleNamespace

from app.services.scoring import calculate_lead_score, calculate_priority


def test_empty_lead_score_is_zero():
    lead = SimpleNamespace(
        name=None,
        email=None,
        phone=None,
        vehicle_year=None,
        vehicle_make=None,
        vehicle_model=None,
        current_insurance=False,
        coverage_type=None,
        policy_expiry=None,
        urgency=None,
    )

    assert calculate_lead_score(lead) == 0


def test_complete_lead_score_is_100():
    lead = SimpleNamespace(
        name="Ali",
        email="ali@example.com",
        phone="123456789",
        vehicle_year=2022,
        vehicle_make="Toyota",
        vehicle_model="Camry",
        current_insurance=True,
        coverage_type="auto",
        policy_expiry="2026-12-01",
        urgency="immediately",
    )

    assert calculate_lead_score(lead) == 100


def test_high_priority():
    assert calculate_priority(80) == "high"


def test_medium_priority():
    assert calculate_priority(50) == "medium"


def test_low_priority():
    assert calculate_priority(49) == "low"
