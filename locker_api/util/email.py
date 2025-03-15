import base64
from email.utils import formataddr

from config import get_settings
from fastapi import HTTPException
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment


def send(sender, recipient, subject, html_content, is_ups_org=False):
    # Format the sender's name and email address
    sender = formataddr(("Koloni" if not is_ups_org else "UPS Lockers", sender))

    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        html_content=html_content,
    )

    # Initialize the SendGrid API client
    sg = SendGridAPIClient(api_key=get_settings().twilio_sendgrid_api_key)

    try:
        # Send the email
        sg.send(message)
        print("Email sent successfully")
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="There was an error trying to send an email to the user with the email address provided. This incident has been reported.",
        )


def send_csv_file(sender, recipient, subject, html_content, file_content, name):
    # Format the sender's name and email address
    sender = formataddr(("Koloni", sender))

    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        html_content=html_content,
    )

    attached_file = Attachment(
        file_content=base64.b64encode(file_content.encode()).decode(),
        file_name=f"{name}.csv",
        file_type="text/csv",
        disposition="attachment",
    )

    message.attachment = attached_file

    # Initialize the SendGrid API client
    sg = SendGridAPIClient(api_key=get_settings().twilio_sendgrid_api_key)

    response = sg.send(message)

    print(response.status_code)
    print(response.body)
    print(response.headers)
