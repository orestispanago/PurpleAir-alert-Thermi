import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_USER = ""
EMAIL_PASS = ""
EMAIL_RECIPIENTS = ["", ""]


def send_mail(body):
    """Sends mail to multiple recipients if necessary"""
    toaddr = ", ".join(EMAIL_RECIPIENTS)
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = toaddr
    msg["Subject"] = "This is a message sent by my Python script"
    msg.attach(MIMEText(body, "plain"))
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)  # password for the pi mail account
    text = msg.as_string()
    server.sendmail(EMAIL_USER, EMAIL_RECIPIENTS, text)
    server.quit()
    print(f"Sent mail: {body}")
