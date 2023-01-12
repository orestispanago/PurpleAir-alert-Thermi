import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


EMAIL_USER = ""
EMAIL_PASS = ""
EMAIL_RECIPIENTS = ["giokosmopoulos@gmail.com", "akaza@upatras.gr"]


SUBJECT = "Δίκτυο αιωρούμενων σωματιδίων Δήμου Θέρμης"
with open("mail_template.html", "r", encoding="utf-8") as f:
    BODY = f.read()


def send_mail(html_table):
    """Sends mail to multiple recipients if necessary"""
    toaddr = ", ".join(EMAIL_RECIPIENTS)
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = toaddr
    msg["Subject"] = SUBJECT
    # msg.attach(MIMEText(TITLE, "plain"))
    msg.attach(MIMEText(BODY.format(html_table=html_table), "html"))
    # msg.attach(MIMEText(DISCLAIMER, "plain"))
    server = smtplib.SMTP_SSL("smtp.upatras.gr", 465)
    server.login(EMAIL_USER, EMAIL_PASS)
    text = msg.as_string()
    server.sendmail(EMAIL_USER, EMAIL_RECIPIENTS, text)
    server.quit()
    logger.info(f"Mail sent")
