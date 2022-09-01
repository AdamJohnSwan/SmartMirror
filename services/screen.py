import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib
from utils.service import Service
import cec
import datetime
from utils.settings import get_settings

class Screen(Service):

    def __init__(self, service_handler):
        self.service_handler = service_handler
        self.tv = None
        self.is_awake = True
        self.settings = get_settings()
        self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])

    def start_service(self):
        self.snooze_service = self.service_handler.get_service('snooze')
        self.screen_service = self.service_handler.get_service('screen')
        self.alarm_service = self.service_handler.get_service('alarm')

        builder = self.service_handler.get_service('builder')
        self.wrapper = builder.get_object('wrapper')
        try:
            cec.init()
            self.tv = cec.Device(cec.CECDEVICE_TV)
            self.tv.power_on()

        except Exception as e:
            print("Device does not support CEC: " + str(e))

    def start_sleep_timer(self):
        self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])
        self.sleep_timer_check()

    def sleep_timer_check(self):
        if(datetime.datetime.now() > self.sleep_timer and self.is_awake):
            self.sleep_screen()
        else:
            GLib.timeout_add_seconds(20, self.sleep_timer_check)
        
    def wake_screen(self):
		# if the mirror is snoozing then ask the user if they really want to turn it on
        self.snooze_service.check_for_snooze()

        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.wrapper.set_opacity, 1)
        if(self.tv is not None):
            self.tv.power_on()
        self.is_awake = True

    def sleep_screen(self):
        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.wrapper.set_opacity, 0)
        self.is_awake = False
        def turn_off_tv():
            if(self.is_awake == False and self.tv is not None):
                self.tv.standby()
        # turn the tv off after 5 minutes of the screen being asleep
        GLib.timeout_add_seconds(60 * 5, turn_off_tv)