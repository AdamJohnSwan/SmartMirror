import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from datetime import datetime
from actions.settings import get_settings

class Clock():
	def __init__(self, builder, wake_screen):
		self.clock = builder.get_object("clock")
		self.weekday = builder.get_object("weekday")
		self.date = builder.get_object("date")
		self.wake_screen = wake_screen
		self.settings = get_settings()
		self.wake_up_times = None
		self.alarm_triggered = False
		if(self.settings["modules"]["alarm"]):
			try:
				self.wake_up_times = self.settings["alarm"]
			except ValueError:
				print("alarm module is set but no alarm settings exist")
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
		if(self.wake_up_times != None):
			self.check_alarm(now)
		GLib.timeout_add_seconds(30, self.set_time)
	
	def check_alarm(self, now):
		try:
			wake_up_time = self.wake_up_times[now.strftime("%A")]
			if(wake_up_time != False):
				parsed_time = datetime.strptime(wake_up_time, "%H:%M:%S").replace(year=now.year, month=now.month, day=now.day)
				if(now > parsed_time):
					if (self.alarm_triggered == False):
						self.wake_screen()
						self.alarm_triggered = True
				else:
					self.alarm_triggered = False
		except ValueError as e:
			# Either the alarm for the day doesn't exist, or the time is in the wrong format.
			print("Cannot find alarm time for today: " + e)
		
