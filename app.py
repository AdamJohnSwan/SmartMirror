import gi
gi.require_version("Gtk", "3.0")
import cec
import datetime
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from actions.settings import get_settings
from actions.clock import Clock
from actions.weather import Weather
from actions.calendar import Calendar
from actions.sleep import Sleep
from actions.keyword_listener import KeywordListener
from actions.speech import say
class SmartMirror:
	def __init__(self):
		self.settings = get_settings()
		builder = Gtk.Builder()
		builder.add_from_file("views/main.glade")
		window = builder.get_object("window1")
		#window.fullscreen()
		window.connect("destroy", self.destroy)
		provider = Gtk.CssProvider()
		csspath = Gio.File.new_for_path(path="views/views.css")
		provider.load_from_file(csspath)
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		window.show_all()

		#Controls for the tv
		self.tv = None
		try:
			cec.init()
			self.tv = cec.Device(cec.CECDEVICE_TV)
			self.tv.power_on()

		except Exception as e:
			print("Device does not support CEC: " + str(e))

		#Hide the cursor
		display = Gdk.Display.get_default()
		cursor = Gdk.Cursor.new_for_display(display, Gdk.CursorType.LEFT_PTR)
		Gdk.get_default_root_window().set_cursor(cursor)

		self.wrapper = builder.get_object("wrapper")
		self.is_awake = True
		self.is_running = True
		self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])
		self.sleep_timer_check()

		self.sleep = Sleep(builder, self.sleep_screen)
		self.clock = Clock(builder, self.wake_screen)
		self.weather = Weather(builder)
		self.calendar = Calendar(builder)
		
		self.keyword_listener = KeywordListener(builder, self.keyword_callback, self.wake_screen)
		if(self.settings["modules"]["voice"]):
			self.keyword_listener.start()
		self.running = True
		while self.running:
			try:
				Gtk.main_iteration_do(False)
			except KeyboardInterrupt:
				self.destroy()

	def destroy(self, window=None):
		self.keyword_listener.end_listener()
		self.running = False

	def keyword_callback(self, text):
		print(text)
		if (self.sleep.is_checking_for_wakeup):
			if("yes" in text):
				self.sleep.end_check_for_wakeup()
		else:
			if("sleep" in text):
				self.sleep_screen()
			elif("time" in text):
				say(datetime.datetime.now().strftime("%-I:%M%p"))
			elif("calendar" in text):
				self.calendar.set_calendar_to_display(text)
			elif("stop recording" in text):
				pass
			else:
				return True
	
	def sleep_timer_check(self):
		if(datetime.datetime.now() > self.sleep_timer and self.is_awake):
			self.sleep_screen()
		else:
			GLib.timeout_add_seconds(20, self.sleep_timer_check)

	def wake_screen(self):
		# if the mirror is sleeping then ask the user if they really want to turn it on
		self.sleep.check_for_sleep()

		Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.wrapper.set_opacity, 1)
		if(self.is_awake == False and self.tv is not None):
			self.tv.power_on()
		self.is_awake = True
		self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])
		self.sleep_timer_check()

	def sleep_screen(self):
		Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.wrapper.set_opacity, 0)
		self.is_awake = False
		def turn_off_tv():
			if(self.is_awake == False and self.tv is not None):
				self.tv.standby()
		# turn the tv off after 5 minutes of the screen being asleep
		GLib.timeout_add_seconds(60 * 5, turn_off_tv)

if __name__ == '__main__':
	SmartMirror()
	
