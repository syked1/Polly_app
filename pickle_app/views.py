from flask import render_template, flash, redirect, session, url_for,request, jsonify
from pickle_app import app, db, stormpath_manager
from .forms import LoginForm, EventForm, EventDateForm, InvitesForm
from flask_stormpath import login_required, user
from .models import Event, EventInvite, EventDate
import datetime
import twilio.twiml
from twilio.rest import TwilioRestClient
import config

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


@app.route('/')
@app.route('/index')
@login_required
def index():
    application = stormpath_manager.application
    invites = EventInvite.query.filter_by(invited_email = user.email).all()
    admin_events = Event.query.filter_by(admin_email = user.email).all()
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
            admin = user
            events_dict[admin_event.id] = {"event":admin_event,"eventdates":admin_eventdates, "admin":user,  "confirmed_date":None, "replied":True, "attending":True, "past":False}
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
            accounts = application.accounts.search({"email":invited_event.admin_email}) #new line
            admin = accounts[0]                                                         #new line
            #admin = User.query.filter_by(id = invited_event.admin_id).first()
            events_dict[invited_event.id] = {"event":invited_event,"eventdates":invited_eventdates, "admin":admin, "confirmed_date":None, "replied":False, "attending":False, "past":False}
            #check if confirmed
            if invited_event.confirmed:
                for eventdate in invited_eventdates:
                    if eventdate.confirmed:
                        events_dict[invited_event.id]["confirmed_date"] = eventdate.date
                #Check if replied and whether you can make the confirmed date
                    eventinvites = EventInvite.query.filter_by(eventdate_id = eventdate.id, invited_email = user.email)
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
# list of events
        print events_dict[key]["event"].name, "\t", events_dict[key]["admin"].given_name, events_dict[key]["admin"].email
    return render_template("index.html",user = user, events_dict = events_dict, id_date_list = id_date_list)



@app.route('/new-event', methods=['GET', 'POST'])
@login_required
def new_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(name=form.name.data, admin_email = user.email, location = form.location.data, notes = form.notes.data)
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('new_event_date', event_id=event.id))
    return render_template("new_event.html", title="New Event", form = form)

@app.route('/new-event-date/<int:event_id>', methods=['GET', 'POST'])
@login_required
def new_event_date(event_id):
    form = EventDateForm()
    event = Event.query.filter_by(id = event_id).first()
    if form.validate_on_submit():
        dates = form.dates.data
        time = form.time.data
        print "Time" , time
        dates_list = dates.split(",")
        print dates_list, time
        for date in dates_list:
            datetime_string = date + time
            datetime_object = datetime.datetime.strptime(datetime_string, '%d/%m/%Y%H:%M')
            eventdate = EventDate(event_id = event_id, date = datetime_object)
            db.session.add(eventdate)
        db.session.commit()
        return redirect(url_for('invites', event_id=event_id))
    if user.email == event.admin_email:
        if event.invites_sent:
            return "This event has already has invites sent"
        else:
            return render_template("date_picker.html", title="New Event Date", form = form, event = event)
    else:
        return "You are not admin for this event"

@app.route('/send-invite/<int:event_id>', methods=['GET', 'POST'])
@login_required
def send_invite(event_id):
    application = stormpath_manager.application
    event = Event.query.filter_by(id=event_id).first()
    eventdates = EventDate.query.filter_by(event_id = event_id).all()
    if user.email != event.admin_email:
        return "You are not admin for this event"
    elif event.invites_sent:
        return "This event has already has invites sent"
    else: 
        event_invites = EventInvite.query.join(EventDate).filter_by(event_id = event_id).all()
        emails = set([x.invited_email for x in event_invites])
        invited_users = [application.accounts.search({'email': email})[0] for email in emails]
        numbers = [u.custom_data.get('phone_number') for u in invited_users]
        organiser_name = user.given_name
    

        twilio_account_sid = config.TWILIO_ACCOUNT_SID
        twilio_auth_token  = config.TWILIO_SECRET_KEY
        client = TwilioRestClient(twilio_account_sid, twilio_auth_token)
        if len(eventdates) > 1:
            message_body = ("{organiser_name} has invited you to {event_name}. "
                            "Tap the link to let {organiser_name} know which dates you can "
                             "make pickleapp.pythonanywhere.com/event-details/{event_id}")\
                            .format(organiser_name=organiser_name, 
                                    event_name=event.name, event_id=event_id)
        else:
            message_body = ("{organiser_name} has invited you to {event_name}. "
                            "Tap the link to let {organiser_name} if you can make it "
                             "pickleapp.pythonanywhere.com/event-details/{event_id}")\
                            .format(organiser_name=organiser_name, 
                                    event_name=event.name, event_id=event_id)

        for number in numbers:
            message = client.messages.create(
                body = message_body,
                to=number,
                from_="+441277420372"
                )

        #Once sent - set the invites sent to true
        event.invites_sent = True
        db.session.add(event)
        db.session.commit()

        return redirect(url_for('index'))



@app.route('/invites/<int:event_id>', methods=['GET', 'POST'])
@login_required
def invites(event_id):
    form = InvitesForm()
    possible_invites = []
    groups = user.groups
    print groups
    invitable_users = []
    for group in groups:
        accounts = group.accounts
        for acc in accounts:
            if acc.email != user.email:
                invitable_users.append(acc)
    for u in invitable_users:
        name = "%s %s" % (u.given_name, u.surname)
        name_tuple = (u.email, name)
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
                event_invite = EventInvite(eventdate_id = eventdate_id , invited_email=invitee, status = 0)
                db.session.add(event_invite)
        if len(eventdates) <= 1:
            event.confirmed = True
            eventdates[0].confirmed = True
        db.session.add(event)
        db.session.commit()
        # send_invite path invokes twilio text function
        return redirect(url_for('send_invite', event_id=event_id))
    if user.email == event.admin_email:
        if event.invites_sent:
            return "This event has already has invites set"
        else:
            return render_template("invites_test.html", title="Invites", event = event , form = form, eventdates = eventdates, possible_invites = possible_invites)
    else:
        return "You are not admin for this event"

@app.route('/event-details/<int:event_id>', methods=['GET', 'POST'])
@login_required
def event_details(event_id):
    event = Event.query.filter_by(id = event_id).first()
    eventdates = EventDate.query.filter_by(event_id = event_id).all()
    eventdates.sort(key = lambda r: r.date)
    invitees = EventInvite.query.join(EventDate).filter_by(event_id = event_id).all()
    invitees_list = []
    application = stormpath_manager.application
    for invitee in invitees:
        invitee_account = application.accounts.search({"email":invitee.invited_email})[0]
        invitees_list.append((invitee,invitee_account))
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
    admin_accounts = application.accounts.search({"email":event.admin_email})
    admin = admin_accounts[0]
    if event.confirmed:
        if event.admin_email == user.email:
            return render_template("event_details_admin_confirmed.html", title="Event_details", event = event , eventdates = eventdates, invitees_list = invitees_list, admin = admin, attendance_dict=attendance_dict)
        elif user.email in [invitee.invited_email for invitee in invitees]:
            return render_template("event_details_invited_confirmed.html", title="Event_details", event = event , eventdates = eventdates, invitees_list = invitees_list, admin = admin, attendance_dict=attendance_dict)
        else:
            return "You are not admin or invited to " + event.name
    elif event.confirmed == False:
        if event.admin_email == user.email:
            return render_template("event_details_admin_not_confirmed.html", title="Event_details", event = event , eventdates = eventdates, invitees_list = invitees_list, admin = admin, attendance_dict=attendance_dict)
        elif user.email in [invitee.invited_email for invitee in invitees]:
            return render_template("event_details_invited_not_confirmed.html", title="Event_details", event = event , eventdates = eventdates, invitees_list = invitees_list, admin = admin)
        else:
            return "You are not admin or invited to " + event.name

@app.route('/confirm-attending/<int:eventinvite_id>', methods=['GET', 'POST'])
@login_required
def confirm_attending(eventinvite_id):
    event_invite = EventInvite.query.filter_by(id = eventinvite_id).first()
    if user.email == event_invite.invited_email:
        event_invite.status = 1
        db.session.add(event_invite)
        db.session.commit()
        return jsonify()
    else:
        return "not authorised"

@app.route('/cant-make-it/<int:eventinvite_id>', methods=['GET', 'POST'])
@login_required
def cant_make_it(eventinvite_id):
    event_invite = EventInvite.query.filter_by(id = eventinvite_id).first()
    if user.email == event_invite.invited_email:
        event_invite.status = -1
        db.session.add(event_invite)
        db.session.commit()
        return jsonify()
    else:
        return "not authorised"

@app.route('/confirm-date/<int:eventdate_id>', methods=['GET', 'POST'])
@login_required
def confirm_date(eventdate_id):
    chosen_eventdate = EventDate.query.filter_by(id = eventdate_id).first()
    eventdates = EventDate.query.filter_by(event_id = chosen_eventdate.event_id)
    if user.email == chosen_eventdate.event.admin_email:
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


@app.route('/confirm-event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def confirm_event(event_id):
    event = Event.query.filter_by(id = event_id).first()
    if event.confirmed:
        return 'This event is already confirmed'
    elif user.email == event.admin_email:
        eventdate = EventDate.query.filter(EventDate.event_id == event_id).filter(EventDate.confirmed == True).first()
        date_string = custom_strftime('%B {S}, %Y', eventdate.date)
        event.confirmed = True
        application = stormpath_manager.application
        event_invites = EventInvite.query.join(EventDate).filter_by(event_id = event_id).all()
        emails = set([x.invited_email for x in event_invites])
        invited_users = [application.accounts.search({'email': email})[0] for email in emails]
        numbers = [u.custom_data.get('phone_number') for u in invited_users]
        organiser_name = user.given_name
        twilio_account_sid = config.TWILIO_ACCOUNT_SID
        twilio_auth_token  = config.TWILIO_SECRET_KEY
        client = TwilioRestClient(twilio_account_sid, twilio_auth_token)
        for number in numbers:
            message = client.messages.create(
            body=("{event_name} is confirmed! pickleapp.pythonanywhere.com/event-details/{event_id}"
                  .format(event_name=event.name, event_id = event.id )), 
            to=number,
            from_="+441277420372")

        #Once sent - set the invites sent to true
        event.invites_sent = True
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('index'))


        db.session.add(event)
        db.session.commit()
        return redirect(url_for("event_details", event_id = chosen_event.id))
    else:
        return "You are not the admin for this event"

@app.route('/delete-event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def delete_event(event_id):
    event_to_delete = Event.query.filter_by(id = event_id).first()
    if user.email == event_to_delete.admin_email:
        event_to_delete.deleted = True
        db.session.add(event_to_delete)
        db.session.commit()
        return redirect(url_for("index"))
    else:
        return "you are not the admin for this event"

@app.route('/delete-eventdate/<int:eventdate_id>', methods=['GET', 'POST'])
@login_required
def delete_eventdate(eventdate_id):
    eventdate_to_delete = EventDate.query.filter_by(id = eventdate_id).first()
    print eventdate_to_delete
    if user.email == eventdate_to_delete.event.admin_email:
        if eventdate_to_delete.event.invites_sent:
            return "Cannot delete eventdate as invites already sent"
        else:
            db.session.delete(eventdate_to_delete)
            db.session.commit()
            return redirect(url_for("new_event_date", event_id=eventdate_to_delete.event.id))
    else:
        return "you are not the admin for this event"
