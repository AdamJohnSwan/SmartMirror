import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GLib
from datetime import datetime
from datetime import date
from utils.settings import get_settings
from utils.google_api_helper import get_credentials
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
import icalendar
import caldav
import requests
from utils.service import Service

MAX_EVENTS = 5

class CalendarEvent():
	def __init__(self, event):
		self.summary: str = event["summary"]
		self.start: datetime = event["start"]
		self.end: datetime = event["end"]

class CalendarEntity():
	def __init__(self, calendar):
		self.calendar = calendar
		self.events = []
		self.old_events = []
	
	def add_event(self, event):
		# convert from date to datetime if needed
		if(type(event["start"]) is date):
			event["start"] = datetime(event["start"].year, event["start"].month, event["start"].day)
		if(type(event["end"]) is date):
			event["end"] = datetime(event["end"].year, event["end"].month, event["end"].day)
		self.events.append(CalendarEvent(event))
		self.events.sort(key = lambda e: e.start.timestamp())

	def get_recent_events(self):
		# remove events that occured after the current time
		events = [e for e in self.events if e.start.timestamp() > datetime.now().timestamp()]
		return events[:MAX_EVENTS]

	def clear_events(self):
		self.old_events = self.events
		self.events = []

class Calendar(Service):
	def __init__(self, service_handler):
		self.service_handler = service_handler

		self.settings = get_settings()
		self.calendar_container = None
		self.calendars = {}
		self.calendar_group_containers = {}
		self.display_group = "default"
	
	def start_service(self):
		builder = self.service_handler.get_service('builder')

		self.calendar_container = builder.get_object("calendar-container")
		if(self.settings["modules"]["calendar"]):
			self.get_calendar_data()
			# update every 30 minutes
			GLib.timeout_add_seconds(1800, self.get_calendar_data)
		else:
			self.calendar_container.hide()
	
	def set_calendar_to_display(self, text_to_check):
		for calendar_key in self.calendars.keys():
			if (calendar_key.lower() in text_to_check.lower()):
				print(f"Displaying calendar {calendar_key}")
				self.display_group = calendar_key
				break
		
	def get_calendar_data(self):
		try:
			# clear out any previous events since new ones are going to be retrieved.
			for calendar_key in self.calendars.keys():
				print(f"Clearing events for calendar group {calendar_key}.")
				self.calendars[calendar_key].clear_events()
			for calendar in self.settings["calendars"]:
				cal_type = calendar["type"]
				if(cal_type == "ics"):
					self.get_ics_calendar_data(calendar)
				elif(cal_type == "webdav"):
					self.get_webdav_calendar_data(calendar)
				elif(cal_type == "google"):
					self.get_google_calendar_data(calendar)
				elif(cal_type == "outlook"):
					pass
			self.create_calendar_display()
		finally:
			return True

	def get_ics_calendar_data(self, calendar):
		try:
			print(f"getting information for calendar {calendar['name']}")
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
					self.calendars[group] = CalendarEntity(calendar)
				for component in content.walk("VEVENT"):
					# add the event to a calendar inside a group. All calendar events in a group will show up on the same screen
					self.calendars[group].add_event({
						"summary": str(component.get('summary')),
						"start": component.get('dtstart').dt,
						"end": component.get('dtend').dt
					})
			else:
				print("Status code not 200 when retrieving ical from server: " + str(res))
		except KeyError as e:
			print("settings missing key: " + str(e))
		except Exception as e:
			print(f"Error getting calendar {calendar['name']} information: {str(e)}")

	def get_webdav_calendar_data(self, calendar):
		try:
			print(f"getting information for calendar {calendar['name']}")
			group = None
			client = caldav.DAVClient(url=calendar["url"], username=calendar["username"], password=calendar["password"])
			webcal = client.principal().calendar(name=calendar['calendar_name'])

			# Create a default group if the group is not specified in settings
			if "group" in calendar:
				group = calendar["group"]
			else:
				group = "default"
			if(group not in self.calendars or self.calendars[group] == None):
				self.calendars[group] = CalendarEntity(calendar)

			events = webcal.date_search(datetime.now(), expand=False)
			for event in events:
				for component in event.icalendar_instance.walk("VEVENT"):
					self.calendars[group].add_event({
						"summary": str(component.get('summary')),
						"start": component.get('dtstart').dt,
						"end": component.get('dtend').dt
					})
		except KeyError as e:
			print("settings missing key: " + str(e))
		except caldav.lib.error.NotFoundError as e:
			print("Calendar does not exist: " + str(e))
		except Exception as e:
			print(f"Error getting calendar {calendar['name']} information: {str(e)}")

	def get_google_calendar_data(self, calendar):
		try:
			print(f"getting information for calendar {calendar['name']}")
			service = get_credentials(calendar["credentials_path"])
			now = datetime.utcnow().isoformat() + 'Z'
			group = None
			if "group" in calendar:
				group = calendar["group"]
			else:
				group = "default"
			if(group not in self.calendars or self.calendars[group] == None):
				self.calendars[group] = CalendarEntity(calendar)

			events_result = service.events().list(calendarId=calendar["calendar_id"], timeMin=now, maxResults=MAX_EVENTS + 1, singleEvents=True, orderBy='startTime').execute()
			events = events_result.get('items', [])

			for event in events:
				start_string_datetime = event["start"].get("dateTime", None)
				start_string_date = event["start"].get("dateTime", None)
				start = None
				if start_string_datetime is not None:
					start = datetime.strptime(start_string_datetime, "%Y-%m-%dT%H:%M:%S%z")
				elif start_string_date is not None:
					start = datetime.strptime(start_string_date, "%Y-%m-%d")
				else:
					print(f"Cannot parse start time for event {event['summary']}")
					continue
				
				end_string_datetime = event["start"].get("dateTime", None)
				end_string_date = event["end"].get("dateTime", None)
				end = None
				if end_string_datetime is not None:
					end = datetime.strptime(end_string_datetime, "%Y-%m-%dT%H:%M:%S%z")
				elif end_string_date is not None:
					end = datetime.strptime(end_string_date, "%Y-%m-%d")
				else:
					print(f"Cannot parse end time for event {event['summary']}")
					continue
				
				self.calendars[group].add_event({
					"summary": event["summary"],
					"start": start,
					"end": end
				})
		except KeyError as e:
			print("settings missing key: " + str(e))
		except HttpError as e:
			print("Http error getting Google event data" + str(e))
		except ValueError as e:
			print("Cannot parse date: " + str(e))
		except RefreshError as e:
			print("Refresh token for calendar is invalid: " + str(e))


	def create_calendar_display(self):
		# remove the old calendar display
		for child in self.calendar_container.get_children():
			child.destroy()
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
				# time is either displayed as just a date or a date and a time
				format = "%I:%M %p %-m/%-d/%y"
				# if the event is at the very start of day then don't display the time. Because the event is more than likely an all-day event.
				if(event.start.hour == 0 and event.start.minute == 0):
					format = "%-m/%-d/%y"
				event_time = event.start.strftime(format)
				display_calendar_container.pack_end(Gtk.Label.new(event_time), False, False, 0)
				self.calendar_group_containers[group_key].pack_start(display_calendar_container, True, True, 0)
			self.calendar_container.pack_start(self.calendar_group_containers[group_key], False, False, 0)
		self.show_calendar()

	def show_calendar(self):
		#only one calendar group can be shown at a time
		for group_key in self.calendars.keys():
			if(group_key == self.display_group):
				self.calendar_group_containers[group_key].show_all()
			else:
				self.calendar_group_containers[group_key].hide()



