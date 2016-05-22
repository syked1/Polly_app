from pickle_app import  db , models
import datetime

def clear_db():
    try:
        db.drop_all()
        print "Cleared database"
    except:
        print "Couldn't clear database"

def create_db():
    db.create_all()

def add_user(firstname,surname,email,phone,group, password):
    user = models.User(firstname=firstname, surname = surname, email = email, phone = phone, group = group)
    user.password = password
    db.session.add(user)
    db.session.commit()
    print "added user..." +firstname + " " + surname


def add_pol_dave():
	add_user("Polly","Benton","pollybenton@gmail.com","07678765382",1,"smeg")
	add_user("David","Sykes","david.sykes70@gmail.com","07678765332",1,"smeg")