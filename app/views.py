from flask import render_template, flash, redirect, session, url_for,request, jsonify
from app import app, db
from .forms import LoginForm, EventForm, EventDateForm, InvitesForm
from .models import User, Event, EventInvite, EventDate
from flask.ext.login import login_required, login_user, logout_user, current_user
import datetime

@app.route('/')
@app.route('/index')
@login_required
def index():
	invites = EventInvite.query.filter_by(invited_id = current_user.id).all()
	admin_events = Event.query.filter_by(admin_id = current_user.id).all()
	invited_events = []
	#Make a unique list of events invited to
	for invite in invites:
		if invite.eventdate.event not in invited_events:
			invited_events.append(invite.eventdate.event)
	#Create events dictionary to be passed to the template
	events_dict = {}
	#Add admin events to the dictionary
	for admin_event in admin_events:
		print "This is an admin event   ", admin_event.name
		#Check if deleted and invite process completed
		if admin_event.deleted == False and admin_event.invites_sent:
			admin_eventdates = EventDate.query.filter_by(event_id = admin_event.id).all()
			admin_eventdates.sort(key= lambda r: r.date)
			admin = current_user
			events_dict[admin_event.id] = {"event":admin_event,"eventdates":admin_eventdates, "admin":current_user,  "confirmed_date":None, "replied":True, "attending":True, "past":False}
			#Check if it's been confirmed and if it is in the past or not
			if admin_event.confirmed:
				for eventdate in admin_eventdates:
					if eventdate.confirmed:
						events_dict[admin_event.id]["confirmed_date"] = eventdate.date
						if events_dict[admin_event.id]["confirmed_date"] < datetime.datetime.now():
							events_dict[admin_event.id]["past"] = True
			elif admin_event.confirmed == False:
				if max([a.date for a in admin_eventdates]) <  datetime.datetime.now():
					events_dict[admin_event.id]["past"] = True
	#Add non-admin events				
	for invited_event in invited_events:
		#Check it's not been deleted
		if invited_event.deleted == False:
			invited_eventdates = EventDate.query.filter_by(event_id = invited_event.id).all()
			invited_eventdates.sort(key= lambda r: r.date)
			admin = User.query.filter_by(id = invited_event.admin_id).first()
			events_dict[invited_event.id] = {"event":invited_event,"eventdates":invited_eventdates, "admin":admin, "confirmed_date":None, "replied":False, "attending":False, "past":False}
			#check if confirmed
			if invited_event.confirmed:
				for eventdate in invited_eventdates:
					if eventdate.confirmed:
						events_dict[invited_event.id]["confirmed_date"] = eventdate.date
				#Check if replied and whether you can make the confirmed date
					eventinvites = EventInvite.query.filter_by(eventdate_id = eventdate.id, invited_id = current_user.id)
					for invite in eventinvites:
						if invite.status == 1:
							events_dict[invited_event.id]["replied"] = True
							if eventdate.confirmed:
								events_dict[invited_event.id]["attending"] = True
						if invite.status == -1:
							events_dict[invited_event.id]["replied"] = True
							if eventdate.confirmed:
								events_dict[invited_event.id]["attending"] = False
			#Check if in the past
				if events_dict[invited_event.id]["confirmed_date"] < datetime.datetime.now():
					events_dict[invited_event.id]["past"] = True
			elif invited_event.confirmed == False:
				if max([a.date for a in invited_eventdates]) <  datetime.datetime.now():
					events_dict[invited_event.id]["past"] = True		
	#return list of event_id and date and sort by date
	id_date_list = []
	for key in events_dict:
		if events_dict[key]["event"].confirmed:
			id_date_list.append((key,events_dict[key]["confirmed_date"]))
		else:
			event_dates = events_dict[key]["eventdates"]
			id_date_list.append((key,min([a.date for a in event_dates])))
	id_date_list.sort(key= lambda r: r[1])
	for key in events_dict:
		print events_dict[key]["event"].name, "\t", events_dict[key]["admin"].firstname, events_dict[key]["admin"].id
	return render_template("index.html",user = current_user, events_dict = events_dict, id_date_list = id_date_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email_address.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user)
			return redirect(request.args.get("next") or url_for("index"))
	return render_template('login.html', title='Sign In',form=form)
	
@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('login'))
						   
@app.route('/new_event', methods=['GET', 'POST'])
@login_required
def new_event():
	form = EventForm()
	if form.validate_on_submit():
		event = Event(name=form.name.data, admin_id=current_user.id, location = form.location.data)
		db.session.add(event)
		db.session.commit()
		return redirect(url_for('new_event_date', event_id=event.id))
	return render_template("new_event.html", title="New Event", form = form)

@app.route('/new_event_date/<int:event_id>', methods=['GET', 'POST'])
@login_required
def new_event_date(event_id):
	form = EventDateForm()
	if form.validate_on_submit():
		date = datetime.datetime.strptime(form.date.data, '%m/%d/%Y %I:%M %p')
		eventdate = EventDate(event_id = event_id, date = date)
		db.session.add(eventdate)
		db.session.commit()
		return redirect(url_for('new_event_date', event_id=event_id))
	eventdates = EventDate.query.filter_by(event_id = event_id).all()
	eventdates.sort(key=lambda r: r.date)
	event = Event.query.filter_by(id = event_id).first()
	invites_check = EventInvite.query.join(EventDate).filter_by(event_id = event_id).all()
	if current_user.id == event.admin_id:
		if event.invites_sent:
			return "This event has already has invites sent"		
		else:
			return render_template("new_event_date.html", title="New Event Date", form = form, event = event , eventdates = eventdates)
	else:
		return "You are not admin for this event"

@app.route('/invites/<int:event_id>', methods=['GET', 'POST'])
@login_required
def invites(event_id):
	form = InvitesForm()
	possible_invites = []
	for user in User.query.filter_by(group = current_user.group).all():
		if user != current_user:
			name = "%s %s" % (user.firstname, user.surname)
			name_tuple = (user.id, name)
			possible_invites.append(name_tuple)
	form.invites.choices = possible_invites
	eventdates = EventDate.query.filter_by(event_id = event_id).all()
	event = Event.query.filter_by(id = event_id).first()
	if form.validate_on_submit():
		print "validated"
		invitees = form.invites.data
		for eventdate in eventdates:
			eventdate_id = eventdate.id
			for invitee in invitees:
				event_invite = EventInvite(eventdate_id = eventdate_id , invited_id=invitee, status = 0)
				db.session.add(event_invite)
		event.invites_sent = True
		if len(eventdates) <= 1:
			event.confirmed = True
			eventdates[0].confirmed = True
		db.session.add(event)
		db.session.commit()
		return redirect(url_for('index'))
	if current_user.id == event.admin_id:
		if event.invites_sent:
			return "This event has already has invites set"		
		else:
			return render_template("invites_test.html", title="Invites", event = event , form = form, eventdates = eventdates, possible_invites = possible_invites)
	else:
		return "You are not admin for this event"

@app.route('/event_details/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event_details(event_id):
	event = Event.query.filter_by(id = event_id).first()
	eventdates = EventDate.query.filter_by(event_id = event_id).all()
	eventdates.sort(key = lambda r: r.date)
	invitees = EventInvite.query.join(EventDate).filter_by(event_id = event_id).all()
	attendance_dict = {}
	for eventdate in eventdates:
		attendance_dict[eventdate.id] = {"attending":0,"cant_make_it":0,"not_replied":0}
		for invitee in invitees:
			if invitee.eventdate.id == eventdate.id:
				if invitee.status == 1:
					attendance_dict[eventdate.id]["attending"] = attendance_dict[eventdate.id]["attending"] + 1
				elif invitee.status == -1:
					attendance_dict[eventdate.id]["cant_make_it"] = attendance_dict[eventdate.id]["cant_make_it"] + 1
				elif invitee.status == 0:
					attendance_dict[eventdate.id]["not_replied"] = attendance_dict[eventdate.id]["not_replied"] + 1
	admin = User.query.filter_by(id = event.admin_id).first()
	if event.confirmed:
		return render_template("event_details_confirmed.html", title="Event_details", event = event , eventdates = eventdates, invitees = invitees, admin = admin, attendance_dict=attendance_dict)
	elif event.confirmed == False:
		if event.admin_id == current_user.id:
			return render_template("event_details_admin.html", title="Event_details", event = event , eventdates = eventdates, invitees = invitees, admin = admin, attendance_dict=attendance_dict)
		elif current_user.id in [invitee.invited_id for invitee in invitees]:
			return render_template("event_details_invited.html", title="Event_details", event = event , eventdates = eventdates, invitees = invitees, admin = admin)
		else:
			return "You are not admin or invited to " + event.name

@app.route('/confirm_attending/<int:eventinvite_id>', methods=['GET', 'POST'])
@login_required
def confirm_attending(eventinvite_id):
	event_invite = EventInvite.query.filter_by(id = eventinvite_id).first()
	if current_user.id == event_invite.invited_id:
		event_invite.status = 1
		db.session.add(event_invite)
		db.session.commit()
		return jsonify()
	else:
		return "not authorised"

@app.route('/cant_make_it/<int:eventinvite_id>', methods=['GET', 'POST'])
@login_required
def cant_make_it(eventinvite_id):
	event_invite = EventInvite.query.filter_by(id = eventinvite_id).first()
	if current_user.id == event_invite.invited_id:
		event_invite.status = -1
		db.session.add(event_invite)
		db.session.commit()
		return jsonify()
	else:
		return "not authorised"

@app.route('/confirm_date/<int:eventdate_id>', methods=['GET', 'POST'])
@login_required
def confirm_date(eventdate_id):
	chosen_eventdate = EventDate.query.filter_by(id = eventdate_id).first()
	eventdates = EventDate.query.filter_by(event_id = chosen_eventdate.event_id)
	if current_user.id == chosen_eventdate.event.admin_id:
		for ed in eventdates:
			if ed == chosen_eventdate:
				ed.confirmed = True
				db.session.add(ed)
			else:
				ed.confirmed = False
				db.session.add(ed)
		db.session.commit()
		return jsonify()
	else:
		return "you are not the admin for this event"

@app.route('/confirm_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def confirm_event(event_id):
	chosen_event = Event.query.filter_by(id = event_id).first()
	if current_user.id == chosen_event.admin_id:
		chosen_event.confirmed = True
		db.session.add(chosen_event)
		db.session.commit()
		return redirect(url_for("event_details", event_id = chosen_event.id))
	else:
		return "you are not the admin for this event"

@app.route('/delete_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def delete_event(event_id):
	event_to_delete = Event.query.filter_by(id = event_id).first()
	if current_user.id == event_to_delete.admin_id:
		event_to_delete.deleted = True
		db.session.add(event_to_delete)
		db.session.commit()
		return redirect(url_for("index"))
	else:
		return "you are not the admin for this event"
		
@app.route('/delete_eventdate/<int:eventdate_id>', methods=['GET', 'POST'])
@login_required
def delete_eventdate(eventdate_id):
	eventdate_to_delete = EventDate.query.filter_by(id = eventdate_id).first()
	print eventdate_to_delete
	if current_user.id == eventdate_to_delete.event.admin_id:
		if eventdate_to_delete.event.invites_sent:
			return "Cannot delete eventdate as invites already sent"
		else:
			db.session.delete(eventdate_to_delete)
			db.session.commit()
			return redirect(url_for("new_event_date", event_id=eventdate_to_delete.event.id))
	else:
		return "you are not the admin for this event"