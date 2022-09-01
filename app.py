import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from utils.service_handler import create_service_handler
class SmartMirror:
	def __init__(self):
		builder = Gtk.Builder()
		builder.add_from_file("views/main.glade")
		window = builder.get_object("window1")
		window.fullscreen()
		window.connect("destroy", self.destroy)
		provider = Gtk.CssProvider()
		csspath = Gio.File.new_for_path(path="views/views.css")
		provider.load_from_file(csspath)
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		window.show_all()

		#Hide the cursor
		display = Gdk.Display.get_default()
		cursor = Gdk.Cursor.new_for_display(display, Gdk.CursorType.BLANK_CURSOR)
		Gdk.get_default_root_window().set_cursor(cursor)

		self.service_handler = create_service_handler(builder)

		self.is_running = True
		
		self.running = True
		while self.running:
			try:
				Gtk.main_iteration_do(False)
			except KeyboardInterrupt:
				self.destroy()

	def destroy(self, window=None):
		self.service_handler.stop_all_services()
		self.running = False

if __name__ == '__main__':
	SmartMirror()
	
