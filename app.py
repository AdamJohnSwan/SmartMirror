import gi
gi.require_version("Gtk", "3.0")
import time
import datetime
import multiprocessing
import queue
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from actions.settings import get_settings
from actions.clock import Clock
from actions.weather import Weather
from actions.calendar import Calendar
from actions.keyword_listener import KeywordListener

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
		self.is_running = True
		self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])
		self.sleep_timer_check()

		self.clock = Clock(builder)
		self.weather = Weather(builder)
		self.calendar = Calendar(builder)

		self.listener_icon = builder.get_object("listener-icon")
		self.listener_words = builder.get_object("listener-words")
		self.listener_icon.hide()
		self.listener_words.hide()

		self.keyword_listener = KeywordListener()
		self.tasks = multiprocessing.Queue()
		self.p = None
		self.p = multiprocessing.Process(target=self.main, args=(self.tasks, ))
		self.p.start()
		if(self.settings["modules"]["voice"]):
			self.keyword_listener.run(self.tasks)


	def main(self, tasks):
		i = 0
		while self.is_running:
			print("iter: " + str(i))
			try:
				try:
					task = tasks.get_nowait()
					method = getattr(self, task["task"])
					if("args" in task):
						args = task["args"]
						method(args)
					else:
						method()
				except queue.Empty:
					pass
				except AttributeError:
					print("task contains method that does not exist")
				Gtk.main_iteration_do(True)
				i += 1
			except KeyboardInterrupt:
				self.destroy()

	def destroy(self, window = None):
		if(self.p != None):
			self.keyword_listener.end_listener()
			self.p.join()
		self.is_running = False
	
	def sleep_timer_check(self):
		if(datetime.datetime.now() > self.sleep_timer and self.is_awake):
			self.sleep_screen()
		else:
			GLib.timeout_add_seconds(10, self.sleep_timer_check)

	def set_listener_text(self, text):
		self.listener_words.set_text(text)

	def toggle_listener_icon(self):
		is_visible = self.listener_icon.get_visible()
		if is_visible:
			self.listener_words.set_text("")
			self.listener_words.hide()
			self.listener_icon.hide()
		else:
			self.listener_words.show()
			self.listener_icon.show()

	def wake_screen(self):
		if(self.wrapper.get_opacity() < 1.0):
			opacity = 0
			while (opacity < 1):
				self.wrapper.set_opacity(opacity)
				time.sleep(0.1)
				opacity += 0.1
		self.is_awake = True
		self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])
		self.sleep_timer_check()

	def sleep_screen(self):
		if(self.wrapper.get_opacity() > 0):
			opacity = 1
			while (opacity > 0):
				self.wrapper.set_opacity(opacity)
				time.sleep(0.1)
				opacity -= 0.1
		self.is_awake = False

if __name__ == '__main__':
	SmartMirror()
	
