import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_USER = ""
EMAIL_PASS = ""
EMAIL_RECIPIENTS = ["giokosmopoulos@gmail.com", "orestis.panagopou@upatras.gr"]

SUBJECT = "Δίκτυο αιωρούμενων σωματιδίων Δήμου Θέρμης"
TITLE = """Ενημέρωση για την περιοχή του 2ου Δημοτικού Σχολείου Θέρμης\n\n\
Σας ενημερώνουμε ότι παρατηρήθηκαν οι ακόλουθες υπερβάσεις:\n"""
DISCLAIMER = """Προσοχή: Το παρόν περιέχει προκαταρκτικές και συνεπώς \
ενδεικτικές τιμές για την ποιότητα αέρα \
λόγω των αιωρούμενων σωματιδίων, \
που ενδέχεται να διαφέρουν έως έναν βαθμό \
από τις ακριβείς. \
Τα ακριβή αποτελέσματα των μετρήσεων \
προκύπτουν κατόπιν μεταγενέστερης \
στατιστικής επεξεργασίας των προκαταρκτικών τιμών \
και κατάλληλων διορθώσεων. \
Ως εκ τούτου αυτά σας γνωστοποιούνται σε δεύτερο χρόνο, \
μέσω των αναλυτικών εκθέσεων-αναφορών \
συγκεντρωτικών αποτελεσμάτων.\n
Σημείωση: Το παρόν είναι προϊόν συνεργασίας μεταξύ \
του Δήμου Θέρμης και του Εργαστηρίου \
Φυσικής της Ατμόσφαιρας του Πανεπιστημίου Πατρών. \
Προορίζεται δε αποκλειστικά για ενημέρωση του εκάστοτε \
αποδέκτη και ισχύουν πλήρως οι διατάξεις του \
Νόμου 2121/1993 περί Πνευματικής Ιδιοκτησίας.\n\n
*** Τέλος δελτίου ***\n\n
Εργαστήριο Φυσικής της Ατμόσφαιρας \n
Τμήμα Φυσικής \n
Πανεπιστήμιο Πατρών"""


def send_mail(html_table):
    """Sends mail to multiple recipients if necessary"""
    toaddr = ", ".join(EMAIL_RECIPIENTS)
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = toaddr
    msg["Subject"] = SUBJECT
    msg.attach(MIMEText(TITLE, "plain"))
    msg.attach(MIMEText(html_table, "html"))
    msg.attach(MIMEText(DISCLAIMER, "plain"))
    server = smtplib.SMTP_SSL("smtp.upatras.gr", 465)
    server.login(EMAIL_USER, EMAIL_PASS)  # password for the pi mail account
    text = msg.as_string()
    server.sendmail(EMAIL_USER, EMAIL_RECIPIENTS, text)
    server.quit()
    print("Mail sent")
