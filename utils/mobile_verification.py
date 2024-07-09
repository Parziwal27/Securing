import random
import string
import requests
from bson.objectid import ObjectId
from config.database import temp_users_collection
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv("/home/ronith/Documents/Bootcamp/Programming and Application/Further Advancements on CMS/backend_2/utils/a.env")

account_sid = os.getenv("TWILIO_ACCOUNT_SID", "AC38333c5058bc7adfa03d3069fced8cc5")
auth_token = os.getenv("TWILIO_AUTH_TOKEN", "12748dc22779ba8a825854a8898f30eb")
twilio_number = os.getenv("TWILIO_NUMBER", "+19124060675")  # Replace with your Twilio number
def generate_token():
    return ''.join(random.choices(string.digits, k=6))
def send_verification_sms(mobile):
    token = generate_token()
    
    try:
        # Update the token in the database
        result = temp_users_collection.update_one({'mobile': mobile}, {'$set': {'mobile_token': token}}, upsert=True)
        logger.info(f"Database update result: {result.raw_result}")

        # Send the SMS using requests
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        data = {
            'To': mobile,
            'From': twilio_number,
            'Body': f'Your verification code is: {token}'
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(url, data=data, headers=headers, auth=(account_sid, auth_token))

        # Check for response status
        if response.status_code == 201:
            logger.info(f"Message SID: {response.json().get('sid')}")
            return {"msg": "Verification SMS sent. Check your phone for the verification code."}
        else:
            logger.error(f"Failed to send verification SMS: {response.status_code} - {response.text}")
            return {"msg": "Failed to send verification SMS."}
    except Exception as e:
        logger.error(f"Error sending verification SMS: {e}")
        return {"msg": "Failed to send verification SMS."}

def verify_mobile_token(temp_user, token):
    if temp_user.get('mobile_token') == token:
        try:
            result = temp_users_collection.update_one(
                {'_id': ObjectId(temp_user['_id'])},
                {'$set': {'mobile_verified': True}, '$unset': {'mobile_token': ''}}
            )
            logger.info(f"Verification update result: {result.raw_result}")
            return True
        except Exception as e:
            logger.error(f"Error verifying mobile token: {e}")
            return False
    else:
        logger.info("Token verification failed.")
        return False

