#POPULATE DATABASE WITH SAMPLE DATA

from app import  db , models
import datetime

try:
	db.drop_all()
	print "Cleared database"
except:
	pass


db.create_all()

def add_user(firstname,surname,email,phone,group, password):
	user = models.User(firstname=firstname, surname = surname, email = email, phone = phone, group = group)
	user.password = password
	db.session.add(user)
	db.session.commit()
	print "added user..." +firstname + " " + surname 

def add_event(name,admin_id,location):
	event = models.Event(name=name, admin_id=admin_id, location = location)
	db.session.add(event)
	db.session.commit()
	print "added event..." + name + " " 

def add_event_date(event_id,datetime):
	event_date = models.EventDate(event_id = event_id, date = datetime)
	db.session.add(event_date)
	db.session.commit()
	print "added event date..." + datetime.strftime("%B %d, %Y") + " " 

def add_event_invite(eventdate_id,invited_id):
	event_invite = models.EventInvite(eventdate_id = eventdate_id , invited_id=invited_id, status = 0)
	db.session.add(event_invite)
	db.session.commit()
	print "invited...." + str(invited_id)
	
add_user("Polly", "Benton", "pollybenton@gmail.com","07736667265","Queens", "cat")
add_user("Will","Balfour","w.n.balfour@gmail.com","07775516821","Queens", "dog")
add_user("David","Sykes","david.sykes70@gmail.com","07827289604","Queens", "goose")
add_user("Alex","Bolland","alex.bolland@gmail.com","07866384948","Queens", "rabbit")
add_user("Sara","Boomsma","sara.boomsma@gmail.com","07538493748","Queens", "mole")
add_user("Matt","Amos","matt.amos@gmail.com","07536273849","Queens", "partridge")
add_event("Polly's Birthday", 1, "52 Freedom St")
add_event("Lads night", 2, "The Goat")
add_event_date(1, datetime.datetime(2016,3,26,21,30))
add_event_date(1, datetime.datetime(2016,3,27,21,30))
add_event_date(1, datetime.datetime(2016,3,29,20,30))
add_event_invite(1,2)
add_event_invite(2,2)
add_event_invite(2,2)
add_event_invite(1,3)
add_event_invite(2,3)
add_event_invite(3,3)
add_event_invite(1,4)
add_event_invite(2,4)
add_event_invite(3,4)
add_event_invite(1,5)
add_event_invite(2,5)
add_event_invite(3,5)
add_event_date(2, datetime.datetime(2016,2,26,19,30))
add_event_date(2, datetime.datetime(2016,2,12,21,30))
add_event_invite(4,3)
add_event_invite(4,6)
add_event_invite(5,3)
add_event_invite(5,6)



#QUERYING

def list_events_for_user(user_id):
	my_invites = models.EventInvite.query.filter_by(invited_id = user_id).all()
	my_events = []
	for invite in my_invites:
		my_events.append(invite.eventdate.event)
	my_events_set = set(my_events)
	for event in my_events_set:
		print event.name
	return list(my_events_set)