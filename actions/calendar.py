import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from datetime import datetime
from datetime import date
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
		# convert from date to datetime if needed
		if(isinstance(event["start"], date)):
			event["start"] = datetime(event["start"].year, event["start"].month, event["start"].day)
		if(isinstance(event["end"], date)):
			event["end"] = datetime(event["end"].year, event["end"].month, event["end"].day)
		self.events.append(CalendarEvent(event))
		self.events.sort(key = lambda e: e.start)

	def get_recent_events(self):
		now = datetime.now()
		events = filter(lambda e: e.start > now, self.events)
		events = [e for e in self.events if e.start > datetime.now()]
		return events[:5]

class Calendar():
	def __init__(self, builder):
		self.settings = get_settings()
		self.calendar_container = builder.get_object("calendar-container")
		self.calendars = {}
		self.calendar_group_containers = {}
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
				if(group not in self.calendars or self.calendars[group] == None):
					self.calendars[group] = CalendarEntity(content)
				for component in content.walk():
					if(component.name == "VEVENT"):
						# add the event to a calendar inside a group. All calendar events in a group will show up on the same screen
						self.calendars[group].add_event({
							"summary": str(component.get('summary')),
							"start": component.get('dtstart').dt,
							"end": component.get('dtend').dt
						})
		except KeyError as e:
			print("settings missing key: " + str(e))
		except Exception as e:
			print("Error getting calendar information: " + str(e))


	def create_calendar_display(self):
		for group_key in self.calendars.keys():
			group = self.calendars[group_key]
			self.calendar_group_containers[group_key] = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
			# Display calendar group name followed by all the events in the calendar 
			calendar_title = Gtk.Label.new(group_key)
			calendar_title.set_alignment(0,0)
			context = calendar_title.get_style_context()
			context.add_class("group-name")
			self.calendar_group_containers[group_key].pack_start(calendar_title, True, True, 0)
			for event in group.get_recent_events():
				# Events are summary followed by the time on the same line
				display_calendar_container = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
				context = display_calendar_container.get_style_context()
				context.add_class("calendar-entry")
				display_calendar_container.pack_start(Gtk.Label.new(event.summary), False, False, 0)
				display_calendar_container.pack_end(Gtk.Label.new(event.start.strftime("%-m/%-d/%y")), False, False, 0)
				self.calendar_group_containers[group_key].pack_start(display_calendar_container, True, True, 0)
			self.calendar_container.pack_start(self.calendar_group_containers[group_key], False, False, 0)
		self.show_calendar("default")

	def show_calendar(self, group_to_show):
		#only one calendar group can be shown at a time
		for group_key in self.calendars.keys():
			if(group_key == group_to_show):
				self.calendar_group_containers[group_key].show_all()
			else:
				self.calendar_group_containers[group_key].hide()



