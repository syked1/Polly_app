from pickle_app import db

class Event(db.Model):
	__tablename__ = "events"
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique=False)
	location = db.Column(db.String(120), unique=False)
	admin_email = db.Column(db.String(120), index=True, unique=False)
	deleted = db.Column(db.Boolean, unique=False, default = False)
	notes = db.Column(db.String(200), unique=False)
	invites_sent = db.Column(db.Boolean, unique=False, default = False)
	confirmed = db.Column(db.Boolean, unique=False, default = False)
	eventdates = db.relationship('EventDate', backref=db.backref('event', lazy='select'))  #RELATIONSHIP DECLARATION
	def __repr__(self):
		return '<Event %r>' % (self.name)

class EventDate(db.Model):
	__tablename__ = "eventdates"
	id = db.Column(db.Integer, primary_key=True)
	event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
	date = db.Column(db.DateTime, unique=False)
	confirmed = db.Column(db.Boolean, unique=False, default = False)
	eventinvites = db.relationship('EventInvite', backref=db.backref('eventdate', lazy='select'))  #RELATIONSHIP DECLARATION
	def __repr__(self):
		return '<EventDate %r>' % (self.date)

class EventInvite(db.Model):
	__tablename__ = "eventinvites"
	id = db.Column(db.Integer, primary_key=True)
	eventdate_id = db.Column(db.Integer, db.ForeignKey("eventdates.id"))
	invited_email = db.Column(db.String(120), index=True, unique=False)
	status =  db.Column(db.Integer, unique=False) #1 is attending, 0 is not replied, -1 is not attending

	def __repr__(self):
		return '<EventInvite %r>' % (self.eventdate.event.name)
