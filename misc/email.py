import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl 
from misc import logging
import threading
from misc import config
# --- Configuration ---
jsonConfig = config.config
emailEnabled = jsonConfig['email']['enabled']
baseURL = jsonConfig['app']['baseURL']
smtp_ser = jsonConfig['email']['smtp']['host']
smtp_port = jsonConfig['email']['smtp']['port']
username = jsonConfig['email']['smtp']['username']
password = jsonConfig['email']['smtp']['password']
sender_email = jsonConfig['email']['smtp']['senderEmail']

subject = "verify your traveltime account"

_DEFAULT_CIPHERS = (
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
    'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:'
    '!eNULL:!MD5'
)

if (username == "" or password == "" or sender_email == "" or smtp_port == "" or smtp_ser == ""):
    if emailEnabled:
        logging.log("Email configuration is not set up correctly. Please check your config.json file.", "critical")
    else:
        logging.log("Email configuration is not set up correctly. Please check your config.json file.", "info")



global server
if emailEnabled:
    context = ssl._create_unverified_context()
    server = smtplib.SMTP_SSL(smtp_ser, smtp_port, context=context)
    server.login(username, password)


# --- Load HTML Template ---
with open("misc/templates/emailVerify.html", "r", encoding="utf-8") as f:
    html_template = f.read()

with open("misc/templates/passwordReset.html", "r", encoding="utf-8") as f:
    html_template2 = f.read()

def sendEmail(user_id, subject, html, server):
    part = MIMEText(html, "html")
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = user_id
    msg["Subject"] = subject
    msg.attach(part)
    server.send_message(msg, from_addr="roeder.lucas@proton.me")
    print("Email sent!")
    
def sendVerifyEmail(user_id: str, verify: str):
    url = f"{baseURL}/user/{user_id}/verify/{verify}"
    html_content = html_template.replace("{{URL}}", url)
    x = threading.Thread(target=sendEmail, args=(user_id, subject, html_content, server,))
    x.start()   

def sendPasswordResetEmail(user_id: str, verify: str, email:str):
    url = f"{baseURL}/user/{user_id}/reset_pw/{verify}"
    html_content = html_template2.replace("{{URL}}", url)
    x = threading.Thread(target=sendEmail, args=(email, subject, html_content, server,))
    x.start()   

def send2FAEnableEmail(user_id: str, verify: str, email:str):
    url = f"{baseURL}/user/{user_id}/2fa/enable/{verify}"
    html_content = html_template2.replace("{{URL}}", url)
    x = threading.Thread(target=sendEmail, args=(email, subject, html_content, server,))
    x.start()