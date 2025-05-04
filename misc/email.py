import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl 
import threading
# --- Configuration ---
smtp_ser = "127.0.0.1"
smtp_port = 1025
username = "roeder.lucas@proton.me"
password = "U8RROl6MEqdWS77h6o2oKQ"

sender_email = "roeder.lucas@proton.me"
subject = "verify your traveltime account"


_DEFAULT_CIPHERS = (
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
    'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:'
    '!eNULL:!MD5'
)
global server

context = ssl._create_unverified_context()
server = smtplib.SMTP_SSL(smtp_ser, smtp_port, context=context)
server.login(username, password)


# --- Load HTML Template ---
with open("misc/template.html", "r", encoding="utf-8") as f:
    html_template = f.read()

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
    url = f"http://localhost:8000/user/{user_id}/verify/{verify}"
    html_content = html_template.replace("{{URL}}", url)
    x = threading.Thread(target=sendEmail, args=(user_id, subject, html_content, server,))
    x.start()   

