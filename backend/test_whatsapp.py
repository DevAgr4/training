from app.services.whatsapp_service import send_whatsapp_message


response = send_whatsapp_message(
    to_phone="918299426750",
    message_text=(
        "Hello! 👋\n\n"
        "This is a test message from the "
        "Training Reminder Automation System.\n\n"
        "WhatsApp integration is working successfully."
    ),
)

print("WHATSAPP TEST SUCCESSFUL")
print(response)