from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask.ext.bootstrap import Bootstrap
from flask.ext.stormpath import StormpathManager




app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
stormpath_manager = StormpathManager(app)
#login_manager.init_app(app)
bootstrap = Bootstrap(app)



from pickle_app import views, models


