import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl 
from misc import logging
import threading
from misc import config


_DEFAULT_CIPHERS = (
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
    'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:'
    '!eNULL:!MD5'
)


# --- Configuration ---
jsonConfig = config.config
emailEnabled: bool = jsonConfig['email']['enabled']
baseURL: str = jsonConfig['app']['baseURL']
smtp_ser: str = jsonConfig['email']['smtp']['host']
smtp_port: int = jsonConfig['email']['smtp']['port']
username: str = jsonConfig['email']['smtp']['username']
password:str = jsonConfig['email']['smtp']['password']
sender_email: str = jsonConfig['email']['smtp']['senderEmail']
subject_verifyEmail: str = jsonConfig['email']['subjects']['verifyEmail']
subject_resetPassword: str = jsonConfig['email']['subjects']['resetPassword']
subject_enableMFA: str = jsonConfig['email']['subjects']['enableMFA']

global server




if (username == "" or password == "" or sender_email == "" or smtp_port == "" or smtp_ser == ""):
    if emailEnabled:
        logging.log("Email configuration is not set up correctly. Please check your config.json file.", "critical")
    else:
        logging.log("Email configuration is not set up correctly. Please check your config.json file.", "info")




if emailEnabled:
    context = ssl._create_unverified_context()
    server = smtplib.SMTP_SSL(smtp_ser, smtp_port, context=context) # type: ignore
    server.login(username, password)


# --- Load HTML Template ---
with open("misc/templates/emailVerify.html", "r", encoding="utf-8") as f:
    html_template = f.read()

with open("misc/templates/passwordReset.html", "r", encoding="utf-8") as f:
    html_template2 = f.read()

def sendEmail(user_id, subject, html, server=None):
    """Send an email with proper error handling"""
    if not emailEnabled:
        logging.log(f"Email sending disabled. Would send to {user_id}: {subject}", "info")
        return
        
    try:
        part = MIMEText(html, "html")
        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = user_id
        msg["Subject"] = subject
        msg.attach(part)
        
        if server is None:
            context = ssl._create_unverified_context()
            with smtplib.SMTP_SSL(smtp_ser, smtp_port, context=context) as temp_server:
                temp_server.login(username, password)
                temp_server.send_message(msg)
        else:
            server.send_message(msg)
            
        logging.log(f"Email sent to {user_id}", "info")
    except Exception as e:
        logging.log(f"Failed to send email: {str(e)}", "error")

def sendVerifyEmail(user_id: str, verify: str):
    url = f"{baseURL}/user/{user_id}/verify/{verify}"
    html_content = html_template.replace("{{URL}}", url)
    x = threading.Thread(target=sendEmail, args=(user_id, subject_verifyEmail, html_content, server,))
    x.start()   

def sendPasswordResetEmail(user_id: str, verify: str, email:str):
    url = f"{baseURL}/user/{user_id}/reset_pw/{verify}"
    html_content = html_template2.replace("{{URL}}", url)
    x = threading.Thread(target=sendEmail, args=(email, subject_resetPassword, html_content, server,))
    x.start()   

def send2FAEnableEmail(user_id: str, verify: str, email:str):
    url = f"{baseURL}/user/{user_id}/2fa/enable/{verify}"
    html_content = html_template2.replace("{{URL}}", url)
    x = threading.Thread(target=sendEmail, args=(email, subject_enableMFA, html_content, server,))
    x.start()

def sendRewardEmail(user_id: str, reward: str, email:str):
    url = f"{baseURL}/user/{user_id}/reward/{reward}"
    html_content = html_template2.replace("{{URL}}", url)
    x = threading.Thread(target=sendEmail, args=(email, subject_enableMFA, html_content, server,))
    x.start()

