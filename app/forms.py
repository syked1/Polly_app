from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, DateTimeField, PasswordField, SubmitField, DateField, SelectMultipleField
from wtforms.validators import Required, Email, Length


class LoginForm(Form):
	email_address = StringField('email address', validators=[Required(),Length(1,64),Email()])
	password = PasswordField("password", validators = [Required()] )

class EventForm(Form):
	name = StringField("Name", validators=[Required()])

class EventDateForm(Form):
	date = DateField("EventDate", format = '%d-%m-%Y', validators=[Required()])
	time = StringField("EventTime", validators=[Required()] )
	location = StringField('location', validators = [Required()] )
	
class InvitesForm(Form):
	invites = SelectMultipleField("Invites", coerce = int)