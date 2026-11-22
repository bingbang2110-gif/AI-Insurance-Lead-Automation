
from typing import Any
import os
import json

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
    from a user's message using OpenRouter.
    """

    schema = {
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
    }
    # Try up to 2 times if the model returns an empty response
    models_to_try = [
        "openrouter/free",
        "baidu/ernie-5.5-flash-preview:free",
    ]

    last_error = None

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an insurance lead qualification assistant. "
                            "Extract only information explicitly stated in the user's message. "
                            "For every field that is not explicitly stated in the user's message, "
                            "you MUST return null. "
                            "Never infer, assume, invent, or copy information from context. "
                            "Do not generate example, placeholder, company, or default values. "
                            "Convert policy expiry dates to YYYY-MM-DD format. "
                            "If the user provides a clear date such as December 15, 2026, "
                            "extract it as 2026-12-15. "
                            "If the user says only that they currently have insurance, "
                            "set current_insurance to true and return null for every other field."
                        ),
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "insurance_lead",
                        "strict": True,
                        "schema": schema,
                    },
                },
                max_tokens=1500,
            )

            content = response.choices[0].message.content

            if content:
                data = json.loads(content)

            if data.get("urgency") == "immediate":
                data["urgency"] = "immediately"

            return data

        except Exception as exc:
            last_error = exc
            print(
                "AI model error:",
                model_name,
                type(exc).__name__,
                getattr(exc, "status_code", None),
                str(exc)[:500]
            )
            continue

    if last_error:
        raise RuntimeError(
            f"All free AI models failed. Last error: {type(last_error).__name__}"
        ) from last_error

    raise ValueError("All free AI models returned empty responses.")
