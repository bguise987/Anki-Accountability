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
	widget.setGeometry(350, 200, 500, 225)

	# Labels
	nameLabel = QLabel("<b>Your name: </b>")
	nameLabel.setTextFormat(1)
	emailLabel = QLabel("<b>Your email address: </b>")
	emailLabel.setTextFormat(1)
	descLabel = QLabel("Please enter your name and email address so we can place this information on the statistics image.\nThis will put a record of your user information on the statistics page rather than having your progress be anonymous.")
	descLabel.setTextFormat(1)
	descLabel.setWordWrap(True)

	# Text boxes for accepting input
	nameText = QLineEdit()
	nameText.setFixedSize(300, 25)
	emailText = QLineEdit()
	emailText.setFixedSize(300, 25)

	# Button to enter data
	confirmButton = QPushButton("Ok")
	confirmButton.clicked.connect(lambda: storeUserInfo(confirmButton, nameText, emailText, widget))
	confirmButton.setFixedWidth(80)

	# Layout
	layout = QGridLayout(widget)
	layout.addWidget(descLabel, 0, 1)
	layout.addWidget(nameLabel, 1, 0)
	layout.addWidget(nameText, 1, 1)
	layout.addWidget(emailLabel, 2, 0)
	layout.addWidget(emailText, 2, 1)
	layout.addWidget(confirmButton, 3, 1)

	# Set tab order for quick data entry
	widget.setTabOrder(nameText, emailText)
	widget.setTabOrder(emailText, confirmButton)

	# If the user has given us information before, let's try and access it now
	checkFirstTime = None
	try:
		checkFirstTime = mw.col.conf['exist_prof_anki_actbil']
	except KeyError:
		mw.col.conf['exist_prof_anki_actbil'] = False

	if checkFirstTime == True:
		userName = mw.col.conf['first_name_anki_actbil'] + " " + mw.col.conf['last_name_anki_actbil']
		nameText.setText(userName)
		userEmail = mw.col.conf['email_addr_anki_actbil']
		emailText.setText(userEmail)


	# Show the window
	widget.show()

def storeUserInfo(button, nameField, emailField, dialogBox):
	# Use some Regex's to split up the user's name into first and last name
	enteredName = nameField.text().split(' ')
	firstName = enteredName[0]
	lastName = enteredName[1]
	# Get the user's email address
	enteredEmail = emailField.text()



	# Check to see if the user has a profile already
	try:
		checkFirstTime = mw.col.conf['exist_prof_anki_actbil']
	except KeyError:
		mw.col.conf['exist_prof_anki_actbil'] = False

	# Store information to mw.col.conf, as per add on writing guide
	# Note: We don't check to see if a previous profile exists. This allows the user to
	# change his/her email address or name if a previous error was made.
	mw.col.conf['exist_prof_anki_actbil'] = True

	mw.col.conf['first_name_anki_actbil'] = firstName
	mw.col.conf['last_name_anki_actbil'] = lastName
	mw.col.conf['email_addr_anki_actbil'] = enteredEmail

	# Let the collection know that we made a conf change
	mw.col.setMod()

	dialogBox.hide()


def myTodayStats(self, _old):
	txt = _old(self)

	try:
		# Extract user info from use mw.col.conf
		userName = mw.col.conf['first_name_anki_actbil'] + " " + mw.col.conf['last_name_anki_actbil']
		userEmail = mw.col.conf['email_addr_anki_actbil']

		# Grab data on user's progress
		# Some of this code is taken from stats.py within anki

		# Run code to grab the eases data from stats
		#deckStats = mw.col.stats()
		# Due to 'private' methods here, run easeGraph()
		# and extract data we'd like from it's returned text
		#results = deckStats.easeGraph()

		txt += self._title(
			_("Anki Accountability"),
			_("<font size='5'>" + userName + ", " + userEmail + "</font>"))

		# Get some information about the deck
		deckId = mw.col.decks.selected()
		deckName = mw.col.decks.name(deckId)
		cardCount = mw.col.db.scalar("select count() from cards where did is %s" % deckId)

		txt += "<div><b>Deck name: " + deckName + "</b></div>"
		txt += "<div><b>Total cards in deck: </b>" + str(cardCount) + "</div>"
	except KeyError:
		showInfo("ERROR: Anki Accountability cannot find your user profile. This is required to display your progress on the statistics page.<br><br>To display your progress, please supply your user information by going to <br><br>Tools->Enter User Info <br><br>and filling out the required information.")
		pass


	return txt


def displayPreview(recEmail, userEmail, userName):
	# get the number of cards in the current collection, which is stored in
	# the main window
	cardCount = mw.col.cardCount()
	deckId = mw.col.decks.selected()
	deckName = mw.col.decks.name(deckId)
	showInfo("Deck name: %s\n%d cards in deck\nRecipient email: %s\nYour email: %s\nYour name: %s" % (deckName, cardCount, recEmail[0], userEmail[0], userName[0]))


# create a new menu item, "Enter User Info"
action = QAction("Enter User Info", mw)

# set it to call requestInfo when it's clicked
mw.connect(action, SIGNAL("triggered()"), requestInfo)
# and add it to the tools menu
mw.form.menuTools.addAction(action)

# Ensure our data is added to the Anki stats image
try:
	stats.CollectionStats.todayStats = wrap(stats.CollectionStats.todayStats, myTodayStats, "around")
except AttributeError:
	showInfo("Error running Anki Accountability. Please check your Anki version.")
	pass
