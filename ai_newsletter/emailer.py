"""
Email sending module using Gmail SMTP with App Password.
Supports multiple recipients via comma-separated list.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_newsletter(
    html_content: str,
    subject: str,
    recipients: list[str] | None = None
) -> bool:
    """
    Send the newsletter via Gmail SMTP to multiple recipients.

    Args:
        html_content: The HTML body of the email
        subject: Email subject line
        recipients: List of recipient emails (defaults to AI_RECIPIENT_EMAILS env var)

    Returns:
        True if sent successfully to all recipients, False otherwise
    """
    gmail_address = os.environ.get("AI_GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("AI_GMAIL_APP_PASSWORD")

    # Parse recipients from env var if not provided
    if recipients is None:
        recipients_str = os.environ.get("AI_RECIPIENT_EMAILS", "")
        recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

    if not gmail_address or not gmail_app_password:
        print("Error: Missing email configuration.")
        print("Required environment variables: AI_GMAIL_ADDRESS, AI_GMAIL_APP_PASSWORD")
        return False

    if not recipients:
        print("Error: No recipients specified.")
        print("Set AI_RECIPIENT_EMAILS environment variable (comma-separated list)")
        return False

    # Create plain text version (fallback)
    plain_text = "This newsletter is best viewed in HTML format."

    success_count = 0
    fail_count = 0

    try:
        # Connect to Gmail SMTP once for all recipients
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_app_password)

            for recipient in recipients:
                try:
                    # Create message for each recipient
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = f"AI Newsletter <{gmail_address}>"
                    msg["To"] = recipient

                    msg.attach(MIMEText(plain_text, "plain"))
                    msg.attach(MIMEText(html_content, "html"))

                    server.send_message(msg)
                    print(f"  Sent to: {recipient}")
                    success_count += 1

                except smtplib.SMTPException as e:
                    print(f"  Failed to send to {recipient}: {e}")
                    fail_count += 1

    except smtplib.SMTPAuthenticationError:
        print("Error: Gmail authentication failed.")
        print("Make sure you're using an App Password, not your regular password.")
        print("See: https://support.google.com/accounts/answer/185833")
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
            <p>The Weekly AI Briefing will be sent to this address every Monday morning.</p>
        </div>
    </body>
    </html>
    """

    return send_newsletter(
        html_content=test_html,
        subject="AI Newsletter - Test Email",
        recipients=recipients
    )


if __name__ == "__main__":
    # Test email sending
    from dotenv import load_dotenv
    load_dotenv()

    print("Sending test email...")
    success = send_test_email()
    if success:
        print("\nTest email sent successfully!")
    else:
        print("\nFailed to send test email.")
