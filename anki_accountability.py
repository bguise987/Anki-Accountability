# Copyright: Ben Guise
# License: GNU GPL v2
# Development funded by the East Asian Languages and Literatures Department 
# at the University of Pittsburgh.


# import the main window object (mw) from ankiqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo

from aqt.utils import getText

# import all of the Qt GUI library
from aqt.qt import *

# We're going to add a menu item below. First we want to create a function to 
# be called when the menu item is activated

recipientEmail = None
userEmail = None

def requestInfo():
	# show a message box and get some info from the user
	#showInfo("Email Progress\n")
	recipientEmail = getText("Please enter recipient's email address:")
	requestUserEmail(recipientEmail)

def requestUserEmail(recEmail):
	userEmail = getText("Please enter your email address:")
	requestUserName(recEmail, userEmail)

def requestUserName(recEmail, userEmail):
	userName = getText("Please enter your name:")
	displayPreview(recEmail, userEmail, userName)

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
