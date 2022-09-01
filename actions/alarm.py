import datetime
from utils.service import Service
from utils.settings import get_settings
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

import pdb;

class Alarm(Service):

    def __init__(self, service_handler):
        self.service_handler = service_handler
        self.settings = get_settings()
        self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])
        self.is_awake = True
        self.wake_up_times = {}
        self.alarm_triggered = False

    def start_service(self):
        self.screen_service = self.service_handler.get_service('screen')
        if(self.settings["modules"]["alarm"]):
            try:
                self.wake_up_times = self.settings["alarm"]
            except ValueError:
                print("alarm module is set but no alarm settings exist")

    def check_alarm(self):
        now = datetime.datetime.now()
        try:
            wake_up_time = self.wake_up_times[now.strftime("%A")]
            if(wake_up_time != False):
                parsed_time = datetime.datetime.strptime(wake_up_time, "%H:%M:%S").replace(year=now.year, month=now.month, day=now.day)
                if(now > parsed_time):
                    if (self.alarm_triggered == False):
                        self.screen_service.wake_screen()
                        self.alarm_triggered = True
                else:
                    self.alarm_triggered = False
        except KeyError as e:
            # Either the alarm for the day doesn't exist, or the time is in the wrong format.
            print("Cannot find alarm time for today: " + str(e))
        except ValueError as e:
            # Either the alarm for the day doesn't exist, or the time is in the wrong format.
            print("Cannot parse time: " + str(e))
    
    