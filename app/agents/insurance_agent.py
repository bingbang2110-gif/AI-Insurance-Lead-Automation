from typing import Any
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def extract_lead_information(message: str) -> dict[str, Any]:
    """
    Extract structured insurance lead information
    from a user's message using OpenAI.
    """

    response = client.responses.create(
        model="openrouter/free",
        input=[
            {
                "role": "system",
                "content": (
                    "You are an insurance lead qualification assistant. "
                    "Extract only information explicitly stated in the user's message. "
                    "For every field that is not explicitly stated in the user's message, "
                    "you MUST return null. "
                    "Never infer, assume, invent, or copy information from context. "
                    "Do not generate example, placeholder, company, or default values. "
                    "If the user says only that they currently have insurance, "
                    "set current_insurance to true and return null for every other field."
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "insurance_lead",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": ["string", "null"]},
                        "email": {"type": ["string", "null"]},
                        "phone": {"type": ["string", "null"]},
                        "vehicle_year": {"type": ["integer", "null"]},
                        "vehicle_make": {"type": ["string", "null"]},
                        "vehicle_model": {"type": ["string", "null"]},
                        "current_insurance": {"type": ["boolean", "null"]},
                        "coverage_type": {"type": ["string", "null"]},
                        "policy_expiry": {"type": ["string", "null"]},
                        "urgency": {"type": ["string", "null"]},
                    },
                    "required": [
                        "name",
                        "email",
                        "phone",
                        "vehicle_year",
                        "vehicle_make",
                        "vehicle_model",
                        "current_insurance",
                        "coverage_type",
                        "policy_expiry",
                        "urgency",
                    ],
                    "additionalProperties": False,
                },
            }
        },
    )

    import json

    return json.loads(response.output_text)