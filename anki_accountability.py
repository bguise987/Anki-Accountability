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


recipientEmail = None
userEmail = None

def requestInfo():
	# show a message box and get some info from the user

	# Setup and show the window
	mw.myWidget = widget = QWidget()
	widget.setWindowTitle("Anki Accountability")
	widget.setGeometry(350, 200, 500, 75)

	# Labels
	nameLabel = QLabel("<b>Your name: </b>")
	nameLabel.setTextFormat(1)
	emailLabel = QLabel("<b>Your email address: </b>")

	# Text boxes for accepting input
	nameText = QTextEdit()
	nameText.setFixedSize(300, 25)
	emailText = QTextEdit()
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

	# Show the window
	widget.show()

def storeUserInfo(button, nameField, emailField):
	storedName = nameField.toPlainText()
	storedEmail = emailField.toPlainText()
	userInfo = storedName + storedEmail
	showInfo("Button clicked!, stored %s" % (userInfo))

	# TODO: Store user info in the DB (use mw.col.conf)
	# TODO: Move this try catch to the main body of this script so it runs at startup

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
