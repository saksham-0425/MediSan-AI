import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv
import os
load_dotenv()

sender_email = os.getenv("EMAIL")
app_password = os.getenv("EMAIL_PASSWORD")

def send_email(receiver_email, subject, body, attachment_path=None):

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content(body)

    if attachment_path:
        with open(attachment_path, "rb") as f:
            file_data = f.read()
            file_name = attachment_path.split("/")[-1]
        msg.add_attachment(file_data, maintype="image", subtype="jpeg", filename=file_name)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)
