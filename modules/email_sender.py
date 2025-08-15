# Handles sending emails to users (welcome and update notifications)

import smtplib
from email.message import EmailMessage
import os
import ssl
from dotenv import load_dotenv # Used to load secure credentials from a .env file

# Load sender email and password from environment variables
load_dotenv()

SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
APP_PASSWORD = os.getenv("EMAIL_PASSWORD")


def send_welcome_email(to_email, name):
    """
    Sends a welcome email to the specified recipient.
    """
    subject = "🎉 You've Subscribed to QHF Updates!"
    body = (
        f"Hi {name},\n\n"
        "Thank you for using the QHF tool!\n\n"
        "You've been successfully subscribed to receive email notifications when new versions are released.\n\n"
        "If you have any questions, feel free to reply to this email.\n\n"
        "Best regards,\n"
        "The QHF Team"
    )

    msg = EmailMessage()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print(f"📧 Welcome email sent to {to_email}")
    except Exception as e:
        print(f"⚠️ Failed to send email to {to_email}: {e}")

def send_update_email(to_email, name):
    subject = "🚀 QHF Tool Update Available!"
    body = (
        f"Hi {name},\n\n"
        "We’ve released an important update for the QHF Tool with new features, improvements, and bug fixes.\n\n"
        "To get the latest version, please visit:\n"
        "https://github.com/rrathore02/QHF-test\n\n"
        "Feel free to reach out with feedback or questions.\n\n"
        "Best regards,\n"
        "The QHF Team"
    )

    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Update email sent to {to_email}")
    except Exception as e:
        print(f"⚠️ Could not send update email to {to_email}: {e}")

