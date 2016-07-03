import os
from config_files import TWILIO

WTF_CSRF_ENABLED = True
SECRET_KEY = 'freedom_st'

basedir = os.path.abspath(os.path.dirname(__file__))
config_dir = "./config_files/"

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

STORMPATH_API_KEY_FILE = os.path.join(config_dir, 'apiKey-4UMJCQQZIF3SDAHA3BR8C0WAZ.properties')
STORMPATH_APPLICATION = 'Pickle'

TWILIO_ACCOUNT_SID = TWILIO.TWILIO_ACCOUNT_SID
TWILIO_SECRET_KEY = TWILIO.TWILIO_KEY