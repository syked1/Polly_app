import datetime
from pickle_app import  db , models
from twilio.rest import TwilioRestClient
import config


def twilio_test_message(to="+447736667265", from_="+441277420372",body="test"):
    twilio_account_sid = config.TWILIO_ACCOUNT_SID
    twilio_auth_token  = config.TWILIO_SECRET_KEY
    client = TwilioRestClient(twilio_account_sid, twilio_auth_token)
    message = client.messages.create(body=body,
    to=to,    # Replace with your phone number
    from_=from_) # Replace with your Twilio number
    print(message.sid)

def clear_db():
    try:
        db.drop_all()
        print "Cleared database"
    except:
        print "Couldn't clear database"

def create_db():
    db.create_all()
    print "Created Database"




