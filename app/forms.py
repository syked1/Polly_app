from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, SubmitField, SelectMultipleField
from wtforms.validators import Required, Email, Length
from wtforms.fields.html5 import DateField, DateTimeField



class LoginForm(Form):
	email_address = StringField('email address', validators=[Required(),Length(1,64),Email()])
	password = PasswordField("password", validators = [Required()] )

class EventForm(Form):
	name = StringField("Event Name", validators=[Required()])
	submit = SubmitField("Pick Dates")

class EventDateForm(Form):
	date = DateField("Event Date")
	#time = DateTimeField("Event Time", format = "%H:%M", validators=[Required()])
	time = StringField("Event Time (HH:MM)", validators=[Required()] )
	location = StringField('Location', validators = [Required()] )
	submit = SubmitField("Save Date Option")
	
class InvitesForm(Form):
	invites = SelectMultipleField("Invites", coerce = int)
	submit = SubmitField("Send Invites")