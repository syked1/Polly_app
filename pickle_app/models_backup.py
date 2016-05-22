from pickle_app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	firstname = db.Column(db.String(64), unique=False)
	surname = db.Column(db.String(64), unique=False)
	email = db.Column(db.String(120), index=True, unique=True)
	phone = db.Column(db.String(120), index=True, unique=True)
	group = db.Column(db.String(64), index=True, unique=False)
	password_hash = db.Column(db.String(128))
	events = db.relationship("Event",backref="user",lazy="select") #RELATIONSHIP DECLARATION
	eventsinvites = db.relationship("EventInvite",backref="user",lazy="select") #RELATIONSHIP DECLARATION

	@property
	def password(self):
		raise AttributeError("password is not a readable attribute")

	@password.setter
	def password(self,password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self,password):
		return check_password_hash(self.password_hash,password)


	def __repr__(self):
		return '<User %r>' % (self.firstname)


class Event(db.Model):
	__tablename__ = "events"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique=False)
	admin_id = db.Column(db.Integer, db.ForeignKey("users.id"))
	eventdates = db.relationship('EventDate', backref=db.backref('event', lazy='select'))  #RELATIONSHIP DECLARATION
	def __repr__(self):
		return '<Event %r>' % (self.name)

class EventDate(db.Model):
	__tablename__ = "eventdates"
	id = db.Column(db.Integer, primary_key=True)
	event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
	date = db.Column(db.DateTime, unique=False)
	location = db.Column(db.String(120), unique=False)
	eventinvites = db.relationship('EventInvite', backref=db.backref('eventdate', lazy='select'))  #RELATIONSHIP DECLARATION
	def __repr__(self):
		return '<EventDate %r>' % (self.date)

class EventInvite(db.Model):
	__tablename__ = "eventinvites"
	id = db.Column(db.Integer, primary_key=True)
	eventdate_id = db.Column(db.Integer, db.ForeignKey("eventdates.id"))
	invited_id = db.Column(db.Integer, db.ForeignKey("users.id"))
	status =  db.Column(db.Integer, unique=False) #1 is attending, 0 is not replied, -1 is not attending

	def __repr__(self):
		return '<EventInvite %r>' % (self.invited_id)