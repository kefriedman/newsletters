"""
Email sending module using Gmail SMTP with App Password.
Reads subscribers from Google Sheets, supports test mode.
"""

import os
import json
import base64
import smtplib
from urllib.parse import urlencode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import gspread
from google.oauth2.service_account import Credentials


def get_sheets_client():
    """Initialize Google Sheets client from credentials."""
    creds_b64 = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_b64:
        return None

    try:
        creds_json = base64.b64decode(creds_b64).decode("utf-8")
        creds_dict = json.loads(creds_json)

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        print(f"Error initializing Google Sheets client: {e}")
        return None


def get_active_subscribers() -> list[str]:
    """Get list of active subscriber emails from Google Sheets."""
    client = get_sheets_client()
    if not client:
        print("Warning: Could not connect to Google Sheets")
        return []

    spreadsheet_id = os.environ.get("AI_SPREADSHEET_ID")
    if not spreadsheet_id:
        print("Warning: AI_SPREADSHEET_ID not set")
        return []

    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.sheet1  # First sheet

        # Get all records
        records = worksheet.get_all_records()

        # Filter for active subscribers
        active_emails = [
            record.get("Email", "").strip()
            for record in records
            if record.get("Status", "").lower() == "active"
            and record.get("Email", "").strip()
        ]

        return active_emails

    except Exception as e:
        print(f"Error reading subscribers: {e}")
        return []


def send_newsletter(
    html_content: str,
    subject: str,
    recipients: list[str] | None = None
) -> bool:
    """
    Send the newsletter via Gmail SMTP.

    In test mode (TEST_MODE=true), only sends to TEST_EMAIL.
    In production mode, sends to all active subscribers from Google Sheets.

    Args:
        html_content: The HTML body of the email
        subject: Email subject line
        recipients: Override recipient list (optional)

    Returns:
        True if sent successfully to all recipients, False otherwise
    """
    gmail_address = os.environ.get("AI_GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("AI_GMAIL_APP_PASSWORD")
    test_mode = os.environ.get("TEST_MODE", "").lower() == "true"

    # Determine recipients
    if test_mode:
        test_email = os.environ.get("TEST_EMAIL")
        if not test_email:
            print("Error: TEST_MODE is true but TEST_EMAIL is not set")
            return False
        recipients = [test_email]
        print(f"[TEST MODE] Sending only to: {test_email}")
    elif recipients is None:
        recipients = get_active_subscribers()
        if not recipients:
            # Fallback to env var if sheets not configured
            recipients_str = os.environ.get("AI_RECIPIENT_EMAILS", "")
            recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

    if not gmail_address or not gmail_app_password:
        print("Error: Missing email configuration.")
        print("Required: AI_GMAIL_ADDRESS, AI_GMAIL_APP_PASSWORD")
        return False

    if not recipients:
        print("Error: No recipients found.")
        return False

    print(f"Sending to {len(recipients)} recipient(s)...")

    plain_text = "This newsletter is best viewed in HTML format."
    success_count = 0
    fail_count = 0

    # Get Apps Script URL for unsubscribe
    apps_script_url = os.environ.get("APPS_SCRIPT_URL", "")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_app_password)

            for recipient in recipients:
                try:
                    # Personalize unsubscribe URL for this recipient
                    personalized_html = html_content
                    if apps_script_url:
                        unsubscribe_params = urlencode({
                            "action": "unsubscribe",
                            "email": recipient,
                            "newsletter": "ai"
                        })
                        unsubscribe_url = f"{apps_script_url}?{unsubscribe_params}"
                        # Replace placeholder with personalized URL
                        personalized_html = html_content.replace(
                            "{{UNSUBSCRIBE_URL}}",
                            unsubscribe_url
                        )

                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = f"What You Need to Know: AI <{gmail_address}>"
                    msg["To"] = recipient

                    msg.attach(MIMEText(plain_text, "plain"))
                    msg.attach(MIMEText(personalized_html, "html"))

                    server.send_message(msg)
                    print(f"  Sent to: {recipient}")
                    success_count += 1

                except smtplib.SMTPException as e:
                    print(f"  Failed to send to {recipient}: {e}")
                    fail_count += 1

    except smtplib.SMTPAuthenticationError:
        print("Error: Gmail authentication failed.")
        print("Make sure you're using an App Password.")
        return False

    except smtplib.SMTPException as e:
        print(f"Error connecting to email server: {e}")
        return False

    print(f"\nSent: {success_count}, Failed: {fail_count}")
    return fail_count == 0


def send_test_email(recipients: list[str] | None = None) -> bool:
    """Send a test email to verify configuration."""
    test_html = """
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; background-color: #0f0f1a; color: #e2e8f0;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #1a1a2e; padding: 30px; border-radius: 12px;">
            <h1 style="color: #667eea; margin-top: 0;">Test Email</h1>
            <p>If you're reading this, your AI Newsletter email configuration is working correctly!</p>
            <p>What You Need to Know: AI will be sent to this address every Monday morning.</p>
        </div>
    </body>
    </html>
    """

    return send_newsletter(
        html_content=test_html,
        subject="What You Need to Know: AI - Test Email",
        recipients=recipients
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("Sending test email...")
    success = send_test_email()
    if success:
        print("\nTest email sent successfully!")
    else:
        print("\nFailed to send test email.")
