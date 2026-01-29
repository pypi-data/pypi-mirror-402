import smtplib
import random
import string
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from termcolor import colored
import pyfiglet
from datetime import datetime

# Email credentials
SENDER_EMAIL = "louatimahdi390@gmail.com"
APP_PASSWORD = "nucm mizw szlu oloq"

def generate_token(length=8):
    """Generate a random token"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def send_verification_email(receiver_email, token):
    """Send verification email with token"""
    message = MIMEMultipart("alternative")
    message["Subject"] = "ATMQL Verification Token"
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email

    # Create the HTML version of the message
    html = f"""
    <html>
    <body>
        <h2>Welcome to ATMQL!</h2>
        <p>Thank you for using our Advanced Topic Modeling Query Language.</p>
        <p>Your verification token is: <strong>{token}</strong></p>
        <p>This token will expire in 10 minutes.</p>
        <br>
        <p>Made with ❤️ by Louati Mahdi</p>
        <p><span class="heartbeat">❤️</span></p>
        <style>
            .heartbeat {{
                animation: heartbeat 1.5s infinite;
            }}
            @keyframes heartbeat {{
                0% {{ transform: scale(1); }}
                25% {{ transform: scale(1.1); }}
                50% {{ transform: scale(1); }}
                75% {{ transform: scale(1.1); }}
                100% {{ transform: scale(1); }}
            }}
        </style>
    </body>
    </html>
    """

    part = MIMEText(html, "html")
    message.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, message.as_string())
        return True
    except Exception as e:
        print(colored(f"Error sending email: {e}", "red"))
        return False

def authenticate_user():
    """Handle user authentication"""
    print(colored(pyfiglet.figlet_format("ATMQL"), "cyan"))
    print(colored("Advanced Topic Modeling Query Language", "yellow"))
    print(colored("Made with ❤️ by Louati Mahdi\n", "magenta"))

    receiver_email = input(colored("Enter your email address: ", "green")).strip()

    if not receiver_email:
        print(colored("Email cannot be empty!", "red"))
        return None

    token = generate_token()
    print(colored("\nSending verification token to your email...", "yellow"))

    if send_verification_email(receiver_email, token):
        print(colored("Verification token sent successfully!", "green"))
        print(colored("Please check your email and enter the token below.\n", "yellow"))

        start_time = time.time()
        attempts = 3

        while attempts > 0:
            user_token = input(colored("Enter verification token: ", "green")).strip()

            if user_token == token:
                end_time = time.time()
                time_spent = round(end_time - start_time, 2)
                print(colored("\nAuthentication successful! Welcome to ATMQL.\n", "green"))

                # Return user info
                return {
                    "email": receiver_email,
                    "sender_email": SENDER_EMAIL,
                    "time_spent": time_spent,
                    "auth_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                attempts -= 1
                print(colored(f"Invalid token! {attempts} attempts remaining.", "red"))

        print(colored("\nToo many failed attempts. Exiting...", "red"))
        return None
    else:
        print(colored("Failed to send verification email. Please try again later.", "red"))
        return None