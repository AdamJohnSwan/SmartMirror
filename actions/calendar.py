import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from gi.repository import Gtk
from datetime import datetime
from actions.settings import get_settings
import icalendar
import requests

class CalendarEvent():
	def __init__(self, event):
		self.summary = event["summary"]
		self.start = event["start"]
		self.end = event["end"]

class CalendarEntity():
	def __init__(self, calendar):
		self.calendar = calendar
		self.events = []
	
	def add_event(self, event):
		self.events.append(CalendarEvent(event))
		self.events.sort(key = lambda e: e.start)

class Calendar():
	def __init__(self, builder):
		self.settings = get_settings()
		self.calendar_container = builder.get_object("calendar-container")
		self.calendars = {}
		self.display_group = None
		if(self.settings["modules"]["calendar"]):
			self.get_calendar_data()
			self.create_calendar_display()
		else:
			self.calendar_container.hide()
		
	def get_calendar_data(self):
		for calendar in self.settings["calendars"]:
			cal_type = calendar["type"]
			if(cal_type == "ics"):
				self.get_ics_calendar_data(calendar)
			elif(cal_type == "google"):
				pass
			elif(cal_type == "outlook"):
				pass

	def get_ics_calendar_data(self, calendar):
		try:
			res = requests.get(calendar["url"])
			if(res.status_code == 200):
				content = icalendar.Calendar.from_ical(res.content)
				group = None
				# Create a default group if the group is not specified in settings
				if "group" in calendar:
					group = calendar["group"]
				else:
					group = "default"
				# If the group doesn't exist yet then create it now to avoid a KeyError
				if(group not in self.calendars):
					self.calendars[group] = {}
				self.calendars[group][calendar["name"]] = CalendarEntity(content)
				for component in content.walk():
					if(component.name == "VEVENT"):
						# add the event to a calendar inside a group. All calendar events in a group will show up on the same screen
						self.calendars[group][calendar["name"]].add_event({
							"summary": str(component.get('summary')),
							"start": component.get('dtstart').dt,
							"end": component.get('dtend').dt
						})
		except KeyError as e:
			print("settings missing key: " + e)
		except Exception as e:
			print("Error getting calendar information: " + e)


	def create_calendar_display(self):
		for group_key in self.calendars.keys():
			group = self.calendars[group_key]
			# Display calendar group name followed by all the events in the calendar 
			self.calendar_container.pack_start(Gtk.Label.new(group_key), False, False, 0)
			for calendar_key in group.keys():
				calendar = group[calendar_key]
				for event in calendar.events:
					# Events are summary followed by the time on the same line
					display_calendar_container = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
					display_calendar_container.pack_start(Gtk.Label.new(event.summary), False, False, 0)
					display_calendar_container.pack_end(Gtk.Label.new(event.start.strftime("%-m/%-d/%y")), False, False, 0)
					self.calendar_container.pack_start(display_calendar_container, True, True, 0)
		self.calendar_container.show_all()


