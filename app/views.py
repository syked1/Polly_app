from flask import render_template, flash, redirect, session, url_for,request
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
	for invite in invites:
		if invite.eventdate.event not in invited_events:
			invited_events.append(invite.eventdate.event)
	events_dict = {}
	for admin_event in admin_events:
		if admin_event.deleted == False:
			admin_eventdates = EventDate.query.filter_by(event_id = admin_event.id).all()
			events_dict[admin_event.id] = {"event":admin_event,"eventdates":admin_eventdates, "confirmed":False, "confirmed_date":None, "admin":True , "replied":True, "attending":True}
			for eventdate in admin_eventdates:
				if eventdate.confirmed:
					events_dict[admin_event.id]["confirmed"] = True
					events_dict[admin_event.id]["confirmed_date"] = eventdate.date
	for invited_event in invited_events:
		if invited_event.deleted == False:
			invited_eventdates = EventDate.query.filter_by(event_id = invited_event.id).all()
			events_dict[invited_event.id] = {"event":invited_event,"eventdates":invited_eventdates, "confirmed":False, "confirmed_date":None, "admin":False , "replied":False, "attending":False}
			for eventdate in invited_eventdates:
				eventinvites = EventInvite.query.filter_by(eventdate_id = eventdate.id, invited_id = current_user.id)
				if eventdate.confirmed:
					events_dict[invited_event.id]["confirmed"] = True
					events_dict[invited_event.id]["confirmed_date"] = eventdate.date
				for invite in eventinvites:
					if invite.status == 1:
						events_dict[invited_event.id]["replied"] = True
						if eventdate.confirmed:
							events_dict[invited_event.id]["attending"] = True
					if invite.status == -1:
						events_dict[invited_event.id]["replied"] = True
						if eventdate.confirmed:
							events_dict[invited_event.id]["attending"] = False
					
	print events_dict
	return render_template("index.html",user = current_user, events_dict = events_dict)

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
		event = Event(name=form.name.data, admin_id=current_user.id)
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
		eventdate = EventDate(event_id = event_id, date = date, location = form.location.data)
		db.session.add(eventdate)
		db.session.commit()
		return redirect(url_for('new_event_date', event_id=event_id))
	eventdates = EventDate.query.filter_by(event_id = event_id).all()
	event = Event.query.filter_by(id = event_id).first()
	return render_template("new_event_date.html", title="New Event Date", form = form, event = event , eventdates = eventdates)

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
		invitees = form.invites.data
		for eventdate in eventdates:
			eventdate_id = eventdate.id
			for invitee in invitees:
				event_invite = EventInvite(eventdate_id = eventdate_id , invited_id=invitee, status = 0)
				db.session.add(event_invite)
		db.session.commit()
		return redirect(url_for('index'))
	return render_template("invites.html", title="Invites", event = event , form = form, eventdates = eventdates, possible_invites = possible_invites)
	
@app.route('/event_details/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event_details(event_id):
	event = Event.query.filter_by(id = event_id).first()
	eventdates = EventDate.query.filter_by(event_id = event_id).all()
	invitees = EventInvite.query.join(EventDate).filter_by(event_id = event_id).all()
	if event.admin_id == current_user.id:
		return render_template("event_details_admin.html", title="Event_details", event = event , eventdates = eventdates, invitees = invitees)
	elif current_user.id in [invitee.invited_id for invitee in invitees]:
		return render_template("event_details_invited.html", title="Event_details", event = event , eventdates = eventdates, invitees = invitees)
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
		return redirect(url_for("event_details", event_id = event_invite.eventdate.event_id))
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
		return redirect(url_for("event_details", event_id = event_invite.eventdate.event_id))
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
		return redirect(url_for("event_details", event_id = chosen_eventdate.event_id))
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