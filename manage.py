import datetime
from pickle_app import  db , models
from twilio.rest import TwilioRestClient
import config

def clear_db():
    try:
        db.drop_all()
        print "Cleared database"
    except:
        print "Couldn't clear database"

def create_db():
    db.create_all()
    print "Created Database"
