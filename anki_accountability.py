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

from anki.hooks import wrap

# imports for methods that we wrap
from anki import stats
from anki import sched
from aqt import main

import time
import re
import sys
# import so we can access SQLite databases outside of usual Anki calls
import sqlite3 as sqlite

# import datetime so we can log the date when a user studies
import datetime as dt
from datetime import timedelta

# import all of the Qt GUI library
from aqt.qt import *

# Some constants
DATABASE_NAME = 'anki_accountability_study.db'
TABLE_NAME = 'anki_accountability'
DB_VER_TABLE = 'db_version'
MAJOR_VERSION = 1
MINOR_VERSION = 0
TIMESTAMP_FORMAT_STR = '%Y-%m-%d'


def requestInfo():
    """Show a message box and get the user's name and email address
    These pieces of information will be stored in the Anki dictionary
    and should sync between installations of Anki """

    # Setup and show the window
    mw.myWidget = widget = QWidget()
    widget.setWindowTitle("Anki Accountability")
    widget.setGeometry(350, 200, 500, 225)

    # Labels
    nameLabel = QLabel("<b>Your name: </b>")
    nameLabel.setTextFormat(1)
    emailLabel = QLabel("<b>Your email address: </b>")
    emailLabel.setTextFormat(1)
    descLabel = QLabel("Please enter your name and email address so we can \
    place this information on the statistics image.\nThis will put a record \
    of your user information on the statistics page rather than having your \
    progress be anonymous.")
    descLabel.setTextFormat(1)
    descLabel.setWordWrap(True)

    # Text boxes for accepting input
    nameText = QLineEdit()
    nameText.setFixedSize(300, 25)
    emailText = QLineEdit()
    emailText.setFixedSize(300, 25)

    # Button to enter data
    confirmButton = QPushButton("Ok")
    confirmButton.clicked.connect(
        lambda: storeUserInfo(confirmButton, nameText, emailText, widget))
    confirmButton.setFixedWidth(80)

    # Layout - create a main layout and then separate it into top and bottom
    # Top will be just the description, bottom will be the form
    mainLayout = QVBoxLayout(widget)

    # Bottom layout items
    bottomLayout = QGridLayout(widget)
    bottomLayout.addWidget(nameLabel, 0, 0)
    bottomLayout.addWidget(nameText, 0, 1)
    bottomLayout.addWidget(emailLabel, 1, 0)
    bottomLayout.addWidget(emailText, 1, 1)
    bottomLayout.addWidget(confirmButton, 2, 1)

    # Add top and bottom layout items into the main layout
    mainLayout.addWidget(descLabel)
    mainLayout.addLayout(bottomLayout)

    # Set tab order for quick data entry
    widget.setTabOrder(nameText, emailText)
    widget.setTabOrder(emailText, confirmButton)

    # If the user has given us information before, let's try and access it now
    checkFirstTime = None
    try:
        checkFirstTime = mw.col.conf['exist_prof_anki_actbil']
    except KeyError:
        mw.col.conf['exist_prof_anki_actbil'] = False

    if checkFirstTime is True:
        userName = (mw.col.conf['first_name_anki_actbil'] +
                    " " + mw.col.conf['last_name_anki_actbil'])
        nameText.setText(userName)
        userEmail = mw.col.conf['email_addr_anki_actbil']
        emailText.setText(userEmail)

    # Show the window
    widget.show()


def storeUserInfo(button, nameField, emailField, dialogBox):
    """ Called from the dialog box created by the requestInfo() method.
         This will check to see if the user has a profile already in the
        mw.col dictionary and then store their information.
        Once the information is stored, it will also close the diaglogBox
        for us. """

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
    # Note: We don't check to see if a previous profile exists. This allows the
    # user to change his/her email address or name if a previous error was
    # made.
    mw.col.conf['exist_prof_anki_actbil'] = True
    mw.col.conf['first_name_anki_actbil'] = firstName
    mw.col.conf['last_name_anki_actbil'] = lastName
    mw.col.conf['email_addr_anki_actbil'] = enteredEmail

    # Let the collection know that we made a conf change
    mw.col.setMod()

    dialogBox.hide()


def myTodayStats(self, _old):
    """ Wrapped version of todayStats. This code will run our modified version
        and then run the original as well """

    txt = _old(self)

    # Check the database version, update if necessary
    checkDBVersion()

    # DB connection code
    con = sqlite.connect(DATABASE_NAME)
    cur = con.cursor()

    # Get the current date
    now = dt.datetime.now()

    # Grab the current deckName and cardCount
    deckId = mw.col.decks.selected()
    deckName = mw.col.decks.name(deckId)
    deckName = formatDeckNameForDatabase(deckName)
    cardCount = mw.col.db.scalar("select count() from cards where did \
                                    is %s" % deckId)

    # Go to the last 7 days and check if there's a DB entry
    for i in range(1, 7):
        prevDate = now - timedelta(days=i)
        prevDate = (str(prevDate.year) + "-" + str(prevDate.strftime('%m')) +
                    "-" + str(prevDate.strftime('%d')))

        # Create the study table (if this is not done, Anki will crash)
        createStudyTable(cur)

        # 	If there is no entry, create one and set to 0
        cur.execute('SELECT * FROM ' + TABLE_NAME + ' WHERE deck_name=? AND\
                    study_date=?', (deckName, prevDate))
        row = str(cur.fetchone())

        # We found a blank study day!
        if (row == 'None'):
            # TODO: Take this out when done:  showInfo("Found none")
            # Store this date into the DB with value of 0
            cur.execute('INSERT INTO ' + TABLE_NAME + '(rowid, deck_name, \
                        study_date, study_complete, card_count) VALUES(NULL, \
                        ?, ?, ?, ?)', (deckName, prevDate, 0, cardCount))

    con.commit()
    con.close()

    try:
        # Extract user info from use mw.col.conf
        userName = (mw.col.conf['first_name_anki_actbil'] + " " +
                    mw.col.conf['last_name_anki_actbil'])
        userEmail = mw.col.conf['email_addr_anki_actbil']

        # Grab data on user's progress
        # Some of this code is taken from stats.py within anki

        # Run code to grab the eases data from stats
        # deckStats = mw.col.stats()
        # Due to 'private' methods here, run easeGraph()
        # and extract data we'd like from it's returned text
        # results = deckStats.easeGraph()

        txt += self._title(
            _("Anki Accountability"),
            _("<font size='5'>" + userName + ", " + userEmail + "</font>"))

        # Get some information about the deck
        deckId = mw.col.decks.selected()
        deckName = mw.col.decks.name(deckId)
        cardCount = mw.col.db.scalar("select count() from cards where did \
                                    is %s" % deckId)

        txt += "<div><b>Deck name: " + deckName + "</b></div>"
        txt += "<div><b>Total cards in deck: </b>" + str(cardCount) + "</div>"
        txt += "<div><b>Studying last 7 days: </b></div>"

        # Grab DB in such a way we can get cols by name
        con = sqlite.connect(DATABASE_NAME)
        con.row_factory = sqlite.Row
        cur = con.cursor()

        for i in range(7, 1, -1):
            prevDate = now - timedelta(days=i)
            prevDate = (str(prevDate.year) + "-" +
                        str(prevDate.strftime('%m')) + "-" +
                        str(prevDate.strftime('%d')))

        deckName = formatDeckNameForDatabase(deckName)
        cur.execute('SELECT * FROM (SELECT study_date, study_complete, \
            card_count FROM ' + TABLE_NAME + ' WHERE deck_name=? ORDER BY \
            study_date DESC LIMIT 7) ORDER BY study_date', (deckName,))

        for row in cur:
            studyCompletion = "null"
            if (row['study_complete'] == 0):
                studyCompletion = "Incomplete"
            else:
                studyCompletion = "Complete"

            txt += ("<div>" + row['study_date'] +
                    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + studyCompletion +
                    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" +
                    str(row['card_count']) + " Cards in deck</div>")

        con.close()

    except KeyError:
        showInfo(
            "ERROR: Anki Accountability cannot find your user profile. This is \
            required to display your progress on the statistics page.<br><br>\
            To display your progress, please supply your user information by \
            going to <br><br>Tools->Enter User Info <br><br>and filling out \
            the required information.")
        pass

    return txt


def myFinishedMsg(self, _old):
    """ New finished message method that will log a complete study session for us
         Store this in prefs.db within the user's
         ~/Documents/Anki/User 1/collection.media directory
         Store date in YYYY-MM-DD format so SQL commands can help us eliminate
         old dates """

    # Grab the current date, split out the parts we want
    now = dt.datetime.now()
    # Format string used so date conforms to SQLite timestamp format
    currDate = now.strftime(TIMESTAMP_FORMAT_STR)

    # Get the deck ID - this will let us look up other information
    deckId = mw.col.decks.selected()

    # Get the parents array
    parents = mw.col.decks.parents(deckId)

    # If len(parents) is 0, we have the parent deck. Get children as
    # (name, deckId) and record studying complete for parent and child decks
    if (len(parents) == 0):
        showInfo("We found a parent deck!")
        children = mw.col.decks.children(deckId)
        for child, childDeckId in children:
            fullChildName = mw.col.decks.name(childDeckId)
            # Split the text by :: since that's how Anki separates
            # parent::child, then only display the child name (childName[1])
            childName = fullChildName.split("::")
            showInfo("Here's a child: " + childName[1])

    # If len(parents) is NOT 0, then we have a child deck. Check the status of
    # the parent deck. If studying is NOT complete for the parent, do nothing.
    # If studying IS complete for the parent, log the studying of this child
    # deck as complete as well.
    if (len(parents) != 0):
        showInfo("We found a child deck!")
        parents = mw.col.decks.parents(deckId)
        for parent in parents:
            showInfo("Here's the parent: " + str(parent))

    deckName = mw.col.decks.name(deckId)
    deckName = formatDeckNameForDatabase(deckName)
    cardCount = mw.col.db.scalar("select count() from cards where did \
                                    is %s" % deckId)

    # Check the database version, update if necessary
    checkDBVersion()

    con = sqlite.connect(DATABASE_NAME)
    cur = con.cursor()
    createStudyTable(cur)

    # Check if we have already made a log of today's session
    # and whether it was 100%
    # TODO: Refactor so that this is a sep. method
    cur.execute('SELECT * FROM ' + TABLE_NAME + ' WHERE deck_name = ? AND \
    study_date = ?', (deckName, currDate))
    row = cur.fetchone()

    # We found a blank study day!
    if (row is None):
        # Store the current date into the database and 100% complete
        studyPercent = 100
        # TODO: Refactor so that this is a separate method
        cur.execute('INSERT INTO ' + TABLE_NAME + '(rowid, deck_name, \
            study_date, study_complete, card_count) VALUES(NULL, ?, ?, ?, ?)',
                    (deckName, currDate, studyPercent, cardCount))
        con.commit()
    else:
        # Not a blank study day--check if study_complete is 100%
        if (row[3] != 100):
            rowId = row['ROWID']
            cur.execute('INSERT OR REPLACE INTO ' + TABLE_NAME +
                        ' VALUES(?, ?, ?, ?, ?)', (rowId, deckName, currDate,
                                                   studyPercent, cardCount))
            con.commit()

    con.close()

    # Run the original method
    _old(self)


def displayPreview(recEmail, userEmail, userName):
    """ Get the number of cards in the current collection, which is stored in
         the main window """
    cardCount = mw.col.cardCount()
    deckId = mw.col.decks.selected()
    deckName = mw.col.decks.name(deckId)
    showInfo("Deck name: %s\n%d cards in deck\nRecipient email: %s\n\
    Your email: %s\nYour name: %s" % (deckName, cardCount, recEmail[0],
                                      userEmail[0], userName[0]))


def formatDeckNameForDatabase(str):
    """ Format the deck name in a consistent manner so that we can store and
    lookup information easily. """
    res = str.replace(" ", "")
    res = res[:30] if len(res) > 30 else res
    return res


# create a new menu item, "Enter User Info"
action = QAction("Enter User Info", mw)

# set it to call requestInfo when it's clicked
mw.connect(action, SIGNAL("triggered()"), requestInfo)

# and add it to the tools menu
mw.form.menuTools.addAction(action)

# Ensure our data is added to the Anki stats image
# by wrapping the existing method
try:
    stats.CollectionStats.todayStats = wrap(stats.CollectionStats.todayStats,
                                            myTodayStats, "around")
except AttributeError:
    showInfo("Error running Anki Accountability. \
    Could not wrap the todayStats method.")
    pass

# Enable logging of a complete study session by wrapping existing method
try:
    sched.Scheduler.finishedMsg = wrap(sched.Scheduler.finishedMsg,
                                       myFinishedMsg, "around")
except AttributeError:
    showInfo("Error running Anki Accountability. \
    Could not wrap the finishedMsg method.")
    pass


# ****************************************************************************
# Database handling functions
# ****************************************************************************

# TODO: Complete DB handling code


def checkDBVersion():
    """ Create (if not exists) DB versioning table """
    con = sqlite.connect(DATABASE_NAME)
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS ' + DB_VER_TABLE + '(ROWID INTEGER \
    PRIMARY KEY, major_version INTEGER NOT NULL, minor_version \
    INTEGER NOT NULL)')

    # 	If there is no entry, create one and set to current versioning
    cur.execute('SELECT * FROM ' + DB_VER_TABLE)
    row = str(cur.fetchone())

    # We found a blank versioning table
    if (row == 'None'):
        cur.execute('INSERT INTO ' + DB_VER_TABLE + '(rowid, major_version, \
        minor_version) VALUES(NULL, ?, ?)', (MAJOR_VERSION, MINOR_VERSION))
        con.commit()

    con.close()


def createStudyTable(cur):
    """ Create the table (and database) that will store study progress """
    cur.execute('CREATE TABLE IF NOT EXISTS ' + TABLE_NAME + '(ROWID INTEGER \
    PRIMARY KEY, deck_name CHAR(30) NOT NULL, study_date CHAR(15) NOT NULL, \
    study_complete INTEGER NOT NULL, card_count INTEGER NOT NULL)')
