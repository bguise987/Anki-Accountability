# Copyright: Ben Guise
# License: GNU GPL v3
# Development funded by the East Asian Languages and Literatures Department
# at the University of Pittsburgh.

# This python script is not part of the add on,
# this is merely used to clean the dictionary so that
# testing can be completed as if the user never installed
# Anki Accountability in the first place without going through
# as much effort to uninstall

# import the main window object (mw) from ankiqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo
# import all of the Qt GUI library
from aqt.qt import *


def dictionaryDelete():
    try:
        mw.col.conf.pop('exist_prof_anki_actbil')
        mw.col.conf.pop('first_name_anki_actbil')
        mw.col.conf.pop('last_name_anki_actbil')
        mw.col.conf.pop('email_addr_anki_actbil')

        mw.col.setMod()

        showInfo("Cleaned out the Anki Accountability parts of the dictionary")
    except KeyError:
        showInfo("Cannot find a key, dictionary must be clean already.")
        pass

# create a new menu item, "Email Results"
action = QAction("Clean dictionary", mw)

# set it to call requestInfo when it's clicked
mw.connect(action, SIGNAL("triggered()"), dictionaryDelete)
# and add it to the tools menu
mw.form.menuTools.addAction(action)
