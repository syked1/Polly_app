from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_bootstrap import Bootstrap
from flask_stormpath import StormpathManager




app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
stormpath_manager = StormpathManager(app)
bootstrap = Bootstrap(app)



from pickle_app import views, models


