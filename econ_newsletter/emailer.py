"""
Email sending module using Gmail SMTP with App Password.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_newsletter(
    html_content: str,
    subject: str,
    recipient: str | None = None
) -> bool:
    """
    Send the newsletter via Gmail SMTP.

    Args:
        html_content: The HTML body of the email
        subject: Email subject line
        recipient: Override recipient (defaults to RECIPIENT_EMAIL env var)

    Returns:
        True if sent successfully, False otherwise
    """
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = recipient or os.environ.get("RECIPIENT_EMAIL")

    if not all([gmail_address, gmail_app_password, recipient]):
        print("Error: Missing email configuration.")
        print("Required environment variables: GMAIL_ADDRESS, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL")
        return False

    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Economics Newsletter <{gmail_address}>"
    msg["To"] = recipient

    # Create plain text version (fallback)
    plain_text = "This newsletter is best viewed in HTML format."

    # Attach both versions
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        # Connect to Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_app_password)
            server.send_message(msg)

        print(f"Newsletter sent successfully to {recipient}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("Error: Gmail authentication failed.")
        print("Make sure you're using an App Password, not your regular password.")
        print("See: https://support.google.com/accounts/answer/185833")
        return False

    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")
        return False


def send_test_email(recipient: str | None = None) -> bool:
    """Send a test email to verify configuration."""
    test_html = """
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1 style="color: #2c3e50;">Test Email</h1>
        <p>If you're reading this, your email configuration is working correctly!</p>
        <p>The Economics Newsletter will be sent to this address every Tuesday.</p>
    </body>
    </html>
    """

    return send_newsletter(
        html_content=test_html,
        subject="Economics Newsletter - Test Email",
        recipient=recipient
    )


if __name__ == "__main__":
    # Test email sending
    from dotenv import load_dotenv
    load_dotenv()

    print("Sending test email...")
    success = send_test_email()
    if success:
        print("Test email sent!")
    else:
        print("Failed to send test email.")
