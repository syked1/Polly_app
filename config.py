WTF_CSRF_ENABLED = True
SECRET_KEY = 'freedom_st'

import os
basedir = os.path.abspath(os.path.dirname(__file__))
config_dir = "/home/pickleapp/app_config"

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

STORMPATH_API_KEY_FILE = os.path.join(config_dir, 'apiKey-4UMJCQQZIF3SDAHA3BR8C0WAZ.properties')
STORMPATH_APPLICATION = 'Pickle'
