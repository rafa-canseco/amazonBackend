import os

import resend
from dotenv import load_dotenv

load_dotenv()
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
resend.api_key = RESEND_API_KEY


def send_email(to: str, subject: str, html_content: str):

    params: resend.Emails.SendParams = {
        "from": "Coinshop <guides@mail.coinshop.world>",
        "to": [to],
        "subject": subject,
        "html": html_content,
    }

    try:
        email = resend.Emails.send(params)
        return {
            "success": True,
            "message": "Email sent successfully",
            "email_id": email["id"],
        }
    except Exception as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}
