import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


EMAIL_USER = ""
EMAIL_PASS = ""
EMAIL_RECIPIENTS = [
    "giokosmopo@upatras.gr",
    "akaza@upatras.gr",
    "sylgo2thermi@gmail.com",
    "mail@2dim-therm.thess.sch.gr",
    "grigoriadoumaria100@gmail.com",
    "e.adamopoulou@thermi.gov.gr",
]


SUBJECT = "Δίκτυο αιωρούμενων σωματιδίων Δήμου Θέρμης"

dirname = os.path.dirname(__file__)
mail_template = os.path.join(dirname, "mail_template.html")

with open(mail_template, "r", encoding="utf-8") as f:
    BODY = f.read()


def send_mail(html_table):
    """Sends mail to multiple recipients if necessary"""
    toaddr = ", ".join(EMAIL_RECIPIENTS)
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = toaddr
    msg["Subject"] = SUBJECT
    msg.attach(MIMEText(BODY.format(html_table=html_table), "html"))
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)
    text = msg.as_string()
    server.sendmail(EMAIL_USER, EMAIL_RECIPIENTS, text)
    server.quit()
    logger.info(f"Mail sent")
