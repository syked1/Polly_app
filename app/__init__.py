from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.bootstrap import Bootstrap

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"   #sets the login view to be the login_manager endpoint.


app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
login_manager.init_app(app)
bootstrap = Bootstrap(app)

from app import views, models


