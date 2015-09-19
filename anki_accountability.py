# Copyright: Ben Guise
# License: GNU GPL v3
# Development funded by the East Asian Languages and Literatures Department 
# at the University of Pittsburgh.

# Some code and conventions borrowed from the Anki Progress Graph add on

# Anki Accountability
###################################################################

# import the main window object (mw) from ankiqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo

#from anki.utils import json

from aqt.utils import getText

from anki import stats
from anki.hooks import wrap
import time, re, sys

# import all of the Qt GUI library
from aqt.qt import *


def requestInfo():
	# Show a message box and get some info from the user

	# Setup and show the window
	mw.myWidget = widget = QWidget()
	widget.setWindowTitle("Anki Accountability")
	widget.setGeometry(350, 200, 500, 75)

	# Labels
	nameLabel = QLabel("<b>Your name: </b>")
	nameLabel.setTextFormat(1)
	emailLabel = QLabel("<b>Your email address: </b>")

	# Text boxes for accepting input
	nameText = QLineEdit()
	nameText.setFixedSize(300, 25)
	emailText = QLineEdit()
	emailText.setFixedSize(300, 25)

	# Button to enter data
	confirmButton = QPushButton("Ok")
	confirmButton.clicked.connect(lambda: storeUserInfo(confirmButton, nameText, emailText))
	confirmButton.setFixedWidth(80)

	# Layout
	layout = QGridLayout(widget)
	layout.addWidget(nameLabel, 0, 0)
	layout.addWidget(nameText, 0, 1)
	layout.addWidget(emailLabel, 1, 0)
	layout.addWidget(emailText, 1, 1)
	layout.addWidget(confirmButton, 2, 1)

	# Set tab order for quick data entry
	widget.setTabOrder(nameText, emailText)
	widget.setTabOrder(emailText, confirmButton)

	# Show the window
	widget.show()

def storeUserInfo(button, nameField, emailField):
	showInfo("Button clicked!, took in %s" % (nameField.text()))

	# TODO: Use some Regex's to split up the user's name into first and last name
	#enteredName = nameField.text()
	enteredName = nameField.text().split(' ')
	firstName = enteredName[0]
	lastName = enteredName[1]
	# TODO: Use some Regex's to split up the user's email into username and domain name
	enteredEmail = emailField.text()
	#enteredEmail = emailField.text().split('@')
	#emailAddr = enteredEmail[0]
	#emailDomain = enteredEmail[1]

	# TODO: Store user info in the DB
	#showInfo("Now about to create the DB")
	#mw.col.db.execute("CREATE TABLE IF NOT EXISTS AnkiAccountabilityUser (id INTEGER PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL, email TEXT NOT NULL)")

	#params = (firstName, lastName, enteredEmail)
	#showInfo("Now creating the query string")

	#firstName = "\"" + firstName + "\""
	#lastName = "\"" + lastName + "\""
	#enteredEmail = "\"" + enteredEmail + "\""

	#query_str = "INSERT INTO AnkiAccountabilityUser VALUES (%s, %s, %s)" % (firstName, lastName, enteredEmail)

	#showInfo("About to execute: " + query_str)

	# Store information to mw.col.conf, as per add on writing guide

	showInfo("Now attempting to store to mw.col.conf")
	conf = mw.col.conf

	# Check to see if the user has a profile already

	showInfo("Check to see if user has a profile already")

	try:
		checkFirstTime = conf['exist_prof_anki_actbil']
	except KeyError:
		conf['exist_prof_anki_actbil'] = False


	if conf['exist_prof_anki_actbil'] == True:
		showInfo("User has already saved!")
	else:
		showInfo("No User profile found, let's create one!")

	conf['exist_prof_anki_actbil'] = True

	conf['first_name_anki_actbil'] = firstName
	conf['last_name_anki_actbil'] = lastName
	conf['email_addr_anki_actbil'] = enteredEmail
	storedConfName = conf['first_name_anki_actbil']
	showInfo("Stored this to conf: %s" % (storedConfName))
	


	#mw.col.db.execute(query_str)
	#mw.col.db.execute("INSERT INTO AnkiAccountabilityUser VALUES(?, ?, ?)", firstName, lastName, enteredEmail)

	# Show that these values were really stored
	#showInfo("Now going to query database")
	#name = mw.col.db.scalar("SELECT * FROM AnkiAccountabilityUser WHERE last_name IS \"Guise\"")
	#if name is None:
	#	showInfo("This is the name that was stored: %s" % (name))
	#else:
	#	showInfo("ERROR: No result found in database")
	#email in mw.col.db.execute("SELECT * FROM AnkiAccountabilityUser WHERE last_name IS \"Guise\"")
	#showInfo("This is the email that was stored: %s" % (email))



	try:
		stats.CollectionStats.todayStats = wrap(stats.CollectionStats.todayStats, myTodayStats, "around")
	except AttributeError:
		showInfo("Error running Anki Accountability. Please check your Anki version.")
		pass

def myTodayStats(self, _old):
    txt = _old(self)
    # TODO: Extract user info from DB (use mw.col.conf)
    txt += "<b>User info goes here</b>"
    return txt
	

def displayPreview(recEmail, userEmail, userName):
	# get the number of cards in the current collection, which is stored in
	# the main window
	cardCount = mw.col.cardCount()
	deckId = mw.col.decks.selected()
	deckName = mw.col.decks.name(deckId)
	showInfo("Deck name: %s\n%d cards in deck\nRecipient email: %s\nYour email: %s\nYour name: %s" % (deckName, cardCount, recEmail[0], userEmail[0], userName[0]))


# create a new menu item, "Email Results"
action = QAction("Email Results", mw)

# set it to call requestInfo when it's clicked
mw.connect(action, SIGNAL("triggered()"), requestInfo)
# and add it to the tools menu
mw.form.menuTools.addAction(action)