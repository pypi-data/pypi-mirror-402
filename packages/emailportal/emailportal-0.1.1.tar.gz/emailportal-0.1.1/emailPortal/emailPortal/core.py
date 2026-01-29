import smtplib
from email.mime.text import MIMEText

GREEN="\033[92m"
RED="\033[91m"
RESET="\033[0m"

def ok(m): print(f"{GREEN}{m}{RESET}")
def err(m): print(f"{RED}{m}{RESET}"); raise SystemExit

class gomail:
    def __init__(self):
        ok("[GOMAIL OBJECT PERFECT CREATED...]")
        self.sender=None
        self.receiver=None
        self.password=None
        self.smtp=None
        self.port=None

def sendGmail(gmail, gomail):
    if "@" not in gmail:
        err("[MESSAGNER GO MAIL NOT FOUNDED...(retry)]")
    gomail.sender=gmail
    ok("[MESSAGNER GO MAIL FOUNDED...]")
    return gomail

def getGmail(gmail, gomail):
    if "@" not in gmail:
        err("[GETTING MAIL NOT FOUNDED...(retry)]")
    gomail.receiver=gmail
    ok("[GETTING MAIL FOUNDED...]")
    return gomail

def apppass(pw, gomail):
    if len(pw) < 10:
        err("[APPPASSWORD NOT FOUNDED...(retry)]")
    gomail.password=pw
    ok("[APPPASSWORD FOUNDED...]")
    return gomail

def smtp(server, port, gomail):
    gomail.smtp=server
    gomail.port=port
    ok("[SMTP FOUNDED...]")
    return gomail

class startModel_server:
    def __init__(self, gomail):
        self.g = gomail

    @property
    def gomail_enter(self):
        try:
            msg = MIMEText("emailPortal test mail")
            msg["From"] = self.g.sender
            msg["To"] = self.g.receiver
            msg["Subject"] = "emailPortal"

            s = smtplib.SMTP(self.g.smtp, self.g.port)
            s.starttls()
            s.login(self.g.sender, self.g.password)
            s.send_message(msg)
            s.quit()

            ok("[STARTMODEL SUCCEFULY STARTED...(succefuly email msg)]")
        except Exception as e:
            err("[STARTMODEL NOT SUCCEFULY STARTED...(retry)]\n" + str(e))