import requests

from app.core.config import settings


def send_whatsapp_message(
    to_phone: str,
    message_text: str | None = None,
    template_name: str = "hello_world",
    language_code: str = "en_US",
    variables: list[str] | None = None,
) -> dict:
    """
    Send a WhatsApp template message through Meta Cloud API.

    Important:
    - template_name must be an approved Meta WhatsApp template.
    - variables are passed as body parameters in the same order
      as the variables configured in the Meta template.
    - message_text is retained for compatibility with the existing
      reminder task, but arbitrary message text is NOT sent as a
      free-form business-initiated WhatsApp message.
    """

    if not to_phone:
        raise ValueError(
            "Recipient WhatsApp number is empty"
        )

    if not settings.WHATSAPP_ACCESS_TOKEN:
        raise ValueError(
            "WhatsApp access token is not configured"
        )

    if not settings.WHATSAPP_API_URL:
        raise ValueError(
            "WhatsApp API URL is not configured"
        )

    if not template_name:
        raise ValueError(
            "WhatsApp template name is required"
        )

    # ---------------------------------------------------------
    # Base template
    # ---------------------------------------------------------

    template = {
        "name": template_name,
        "language": {
            "code": language_code
        },
    }

    # ---------------------------------------------------------
    # Add dynamic template variables
    # ---------------------------------------------------------
    #
    # Meta expects:
    #
    # "components": [
    #     {
    #         "type": "body",
    #         "parameters": [
    #             {
    #                 "type": "text",
    #                 "text": "Rahul"
    #             }
    #         ]
    #     }
    # ]
    #
    # Only add components when variables are supplied.
    # This keeps hello_world working because it has no variables.
    # ---------------------------------------------------------

    if variables:

        parameters = []

        for value in variables:

            parameters.append(
                {
                    "type": "text",
                    "text": str(value),
                }
            )

        template["components"] = [
            {
                "type": "body",
                "parameters": parameters,
            }
        ]

    # ---------------------------------------------------------
    # Complete Meta WhatsApp payload
    # ---------------------------------------------------------

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": template,
    }

    # ---------------------------------------------------------
    # Headers
    # ---------------------------------------------------------

    headers = {
        "Authorization": (
            f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"
        ),
        "Content-Type": "application/json",
    }

    # ---------------------------------------------------------
    # Send request
    # ---------------------------------------------------------

    response = requests.post(
        settings.WHATSAPP_API_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    # ---------------------------------------------------------
    # Handle Meta API errors
    # ---------------------------------------------------------

    if not response.ok:

        raise RuntimeError(
            f"WhatsApp API error "
            f"{response.status_code}: "
            f"{response.text}"
        )

    # ---------------------------------------------------------
    # Parse response
    # ---------------------------------------------------------

    data = response.json()

    print(
        "[WHATSAPP API SUCCESS]"
        f" template={template_name}"
        f" language={language_code}"
        f" response={data}"
    )

    return data