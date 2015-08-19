# Copied from Anki add-on writing guide

# import the main window object (mw) from ankiqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo
# import all of the Qt GUI library
from aqt.qt import *

# We're going to add a menu item below. First we want to create a function to 
# be called when the menu item is activated

def testFunction():
	# get the number of cards in the current collection, which is stored in
	# the main window
	cardCount = mw.col.cardCount()
	deckName = "Test deck"
	deckId = mw.col.decks.selected()
	deckName = mw.col.decks.name(deckId)
	# show a message box
	showInfo("Deck name: %s\n%d cards in deck" % (deckName, cardCount))
	#showInfo("Deck ID: %d" % deckId)
	#showInfo("Card count: %d" % cardCount)

# create a new menu item, "test"
action = QAction("Email Results", mw)

# set it to call testFunction when it's clicked
mw.connect(action, SIGNAL("triggered()"), testFunction)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
