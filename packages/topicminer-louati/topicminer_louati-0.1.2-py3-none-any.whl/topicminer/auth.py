import smtplib
import uuid
import time
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIGURATION ---
SENDER_EMAIL = "louatimahdi390@gmail.com"
APP_PASSWORD = "nucm mizw szlu oloq" 

class AuthManager:
    def __init__(self):
        self.start_time = time.time()
        self.user_email = None
        self.token = None

    def generate_token(self):
        return str(uuid.uuid4())

    def send_token_email(self, user_email):
        self.user_email = user_email
        self.token = self.generate_token()
        
        subject = "Your TopicMiner API Key"
        body = f"""
        <html>
        <body>
            <h2 style="color: #2c3e50;">Welcome to TopicMiner!</h2>
            <p>Your access token is:</p>
            <div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; font-size: 20px; font-family: monospace; color: #27ae60; text-align: center;">
                {self.token}
            </div>
            <p>Made With Love By Louati Mahdi</p>
            <div style="font-size: 24px;">❤️</div>
        </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = user_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True, "Token sent successfully to your email."
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

    def verify_token(self, user_token):
        if self.token and user_token == self.token:
            return True
        return False

    def get_usage_metrics(self):
        end_time = time.time()
        time_spent = end_time - self.start_time
        formatted_time = str(datetime.timedelta(seconds=int(time_spent)))
        
        footer = (
            f"\n{'='*60}\n"
            f"User Email: {self.user_email}\n"
            f"Sender Email: {SENDER_EMAIL}\n"
            f"Time Spent: {formatted_time}\n"
            f"Thank you for your loyalty and using the library ❤️\n"
            f"{'❤️' * 10} Made With Love By Louati Mahdi {'❤️' * 10}\n"
            f"{'='*60}\n"
        )
        return footer