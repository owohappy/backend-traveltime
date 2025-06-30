import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl 
from misc import logging
import threading
from misc import config

cfg = config.config

_DEFAULT_CIPHERS = (
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
    'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:'
    '!eNULL:!MD5'
)

email_enabled = cfg['email']['enabled']
base_url = cfg['app']['baseURL']
smtp_host = cfg['email']['smtp']['host']
smtp_port = cfg['email']['smtp']['port']
username = cfg['email']['smtp']['username']
password = cfg['email']['smtp']['password']
sender_email = cfg['email']['smtp']['senderEmail']

server = None

if not all([username, password, sender_email, smtp_port, smtp_host]):
    level = "critical" if email_enabled else "info"
    logging.log("Email config incomplete", level)

if email_enabled:
    context = ssl._create_unverified_context()
    server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
    server.login(username, password)

with open("misc/templates/emailVerify.html", "r", encoding="utf-8") as f:
    verify_template = f.read()

with open("misc/templates/passwordReset.html", "r", encoding="utf-8") as f:
    reset_template = f.read()

def send_email(user_id, subject, html, server=None):
    if not email_enabled:
        logging.log(f"Email disabled. Would send to {user_id}: {subject}", "info")
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
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as temp_server:
                temp_server.login(username, password)
                temp_server.send_message(msg)
        else:
            server.send_message(msg)
            
        logging.log(f"Email sent to {user_id}", "info")
    except Exception as e:
        logging.log(f"Email failed: {e}", "error")

def get_subject(key):
    subjects = cfg.get('email', {}).get('subjects', {})
    defaults = {
        'verification': "Verify Your Email",
        'password_reset': "Password Reset",
        'welcome': "Welcome",
        'notification': "Notification"
    }
    return subjects.get(key, defaults.get(key, "Notification"))

def send_verify_email(user_id, verify_code):
    url = f"{base_url}/user/{user_id}/verify/{verify_code}"
    html = verify_template.replace("{{URL}}", url)
    subject = get_subject('verification')
    t = threading.Thread(target=send_email, args=(user_id, subject, html, server))
    t.start()   

def send_password_reset_email(user_id, verify_code, email):
    url = f"{base_url}/user/{user_id}/reset_pw/{verify_code}"
    html = reset_template.replace("{{URL}}", url)
    subject = get_subject('password_reset')
    t = threading.Thread(target=send_email, args=(email, subject, html, server))
    t.start()   

def send_2fa_enable_email(user_id, verify_code, email):
    url = f"{base_url}/user/{user_id}/2fa/enable/{verify_code}"
    html = reset_template.replace("{{URL}}", url)
    subject = get_subject('enableMFA')
    t = threading.Thread(target=send_email, args=(email, subject, html, server))
    t.start()

def send_reward_email(user_id, reward, email):
    url = f"{base_url}/user/{user_id}/reward/{reward}"
    html = reset_template.replace("{{URL}}", url)
    subject = get_subject('reward')
    t = threading.Thread(target=send_email, args=(email, subject, html, server))
    t.start()

