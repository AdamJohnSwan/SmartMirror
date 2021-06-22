import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from datetime import datetime
from actions.settings import get_settings

class CalendarItem():
	pass

class CalendarEntity():
	pass

class Calendar():
	def __init__(self, builder):
		self.settings = get_settings()
		if(self.settings["modules"]["calendar"]):
			pass
		elif(self.settings["modules"]["holidays"]):
			pass
		else:
			builder.get_object("calendar-container").hide()
		
