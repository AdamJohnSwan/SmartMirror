import gi
from pvporcupine import LIBRARY_PATH
gi.require_version("Gtk", "3.0")
import time
import datetime
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from actions.settings import get_settings
from actions.clock import Clock
from actions.weather import Weather
from actions.calendar import Calendar
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

		self.wrapper = builder.get_object("wrapper")
		self.is_awake = True
		self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])
		self.sleep_timer_check()

		self.clock = Clock(builder)
		self.weather = Weather(builder)
		self.calendar = Calendar(builder)
		
		self.keyword_listener = KeywordListener(builder, self.keyword_callback, self.wake_screen)
		if(self.settings["modules"]["voice"]):
			self.keyword_listener.start()
		#Gtk.main()
		self.running = True
		while self.running:
			Gtk.main_iteration_do(False)

	def destroy(self, window):
		self.keyword_listener.end_listener()
		self.running = False

	def keyword_callback(self, text):
		print(text)
		if("wake" in text):
			self.wake_screen()
		elif("sleep" in text):
			self.sleep_screen()
		elif("time" in text):
			say(datetime.datetime.now().strftime("%-I:%-M%p"))
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
		Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.wrapper.set_opacity, 1)
		self.is_awake = True
		self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])
		self.sleep_timer_check()

	def sleep_screen(self):
		Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.wrapper.set_opacity, 0)
		self.is_awake = False

if __name__ == '__main__':
	SmartMirror()
	
