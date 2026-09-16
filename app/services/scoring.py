def calculate_lead_score(lead):
    """
    Calculate a lead score from 0 to 100.
    """

    score = 0

    # Contact information
    if lead.name:
        score += 10

    if lead.email:
        score += 10

    if lead.phone:
        score += 10

    # Vehicle information
    if (
        lead.vehicle_year
        and lead.vehicle_make
        and lead.vehicle_model
    ):
        score += 15

    # Current insurance
    if lead.current_insurance is True:
        score += 10

    # Coverage
    if lead.coverage_type:
        score += 15

    # Policy expiry
    if lead.policy_expiry:
        score += 10

    # Urgency
    if lead.urgency:
        urgency = lead.urgency.lower()

        if (
            "today" in urgency
            or "immediately" in urgency
            or "within a week" in urgency
        ):
            score += 20
        elif "week" in urgency:
            score += 15
        else:
            score += 5

    return min(score, 100)


def calculate_priority(score):
    """
    Convert lead score into a priority level.
    """

    if score >= 80:
        return "high"

    if score >= 50:
        return "medium"

    return "low"