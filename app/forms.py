from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, DateTimeField, PasswordField, SubmitField, DateField, SelectMultipleField
from wtforms.validators import Required, Email, Length


class LoginForm(Form):
	email_address = StringField('email address', validators=[Required(),Length(1,64),Email()])
	password = PasswordField("password", validators = [Required()] )

class EventForm(Form):
	name = StringField("Event Name", validators=[Required()])
	submit = SubmitField("Pick Dates")

class EventDateForm(Form):
	date = DateField("Event Date (dd-mm-yy)", format = '%d-%m-%Y', validators=[Required()])
	time = StringField("Event Time (HH:MM)", validators=[Required()] )
	location = StringField('Location', validators = [Required()] )
	submit = SubmitField("Save Date Option")
	
class InvitesForm(Form):
	invites = SelectMultipleField("Invites", coerce = int)
	submit = SubmitField("Send Invites")