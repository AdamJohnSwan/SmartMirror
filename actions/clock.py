import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from datetime import datetime
from actions.settings import get_settings

class Clock():
	def __init__(self, builder):
		self.clock = builder.get_object("clock")
		self.weekday = builder.get_object("weekday")
		self.date = builder.get_object("date")
		self.settings = get_settings()
		if(self.settings["modules"]["clock"]):
			self.set_time()
		else:
			builder.get_object("clock-container").hide()
	def set_time(self):
		now = datetime.now()
		current_time = now.strftime("%I:%M %p")
		current_day = now.strftime("%A")
		current_date = now.strftime("%B %-d, %Y")
		self.clock.set_text(current_time)
		self.weekday.set_text(current_day)
		self.date.set_text(current_date)
		GLib.timeout_add_seconds(60, self.set_time)
		
