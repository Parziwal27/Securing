import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
from bson.objectid import ObjectId
from config.database import temp_users_collection

# Function to generate a random token
def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

# Function to send verification email
def send_verification_email(email):
    token = generate_token()

    try:
        # Update the token in the database
        result = temp_users_collection.update_one({'email': email}, {'$set': {'email_token': token}})
        if result.modified_count == 0:
            raise ValueError(f"Email '{email}' not found in database or not updated.")

        # Email content setup
        msg = MIMEMultipart()
        msg['From'] = 'ronithk29@gmail.com'  # Replace with your email address
        msg['To'] = email
        msg['Subject'] = 'CMS Verfication'

        body = f'Your verification token is: {token}'
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Login using your Gmail account
        server.login('ronithk29@gmail.com', 'Ronyk@1234')  # Replace with your email and password

        # Send email
        text = msg.as_string()
        server.sendmail('ronithk29@gmail.com', email, text)
        server.quit()

        print(f"Verification email sent to {email}. Check your inbox.")
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False

# Function to verify email token
def verify_email_token(temp_user, token):
    try:
        if temp_user.get('email_token') == token:
            # Update email verification status in the database
            result = temp_users_collection.update_one(
                {'_id': ObjectId(temp_user['_id'])},
                {'$set': {'email_verified': True}, '$unset': {'email_token': ''}}
            )
            if result.modified_count > 0:
                print("Email verification successful.")
                return True
        print("Token verification failed or document not updated.")
        return False
    except Exception as e:
        print(f"Error verifying email token: {e}")
        return False