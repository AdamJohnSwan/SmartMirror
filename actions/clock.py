import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from datetime import datetime
from utils.settings import get_settings
from utils.service import Service

class Clock(Service):
	def __init__(self, service_handler):

		self.service_handler = service_handler
		self.settings = get_settings()

	def start_service(self):
		builder = self.service_handler.get_service('builder')

		self.alarm_service = self.service_handler.get_service('alarm')
		self.clock = builder.get_object("clock")
		self.weekday = builder.get_object("weekday")
		self.date = builder.get_object("date")

		self.clock_container = builder.get_object("clock-container")

		self.set_time()
		GLib.timeout_add_seconds(30, self.set_time)
	
	def set_time(self):
		try:
			now = datetime.now()
			current_time = now.strftime("%I:%M %p")
			current_day = now.strftime("%A")
			current_date = now.strftime("%B %-d, %Y")
			self.clock.set_text(current_time)
			self.weekday.set_text(current_day)
			self.date.set_text(current_date)
			if(self.settings["modules"]["alarm"]) and self.alarm_service.service_started == True:
				self.alarm_service.check_alarm()
		finally:
			return True
		
