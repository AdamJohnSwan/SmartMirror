import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GLib
import datetime
import requests
from threading import Thread
from utils.settings import get_settings
from utils.service import Service

class ForecastTime():
	def __init__(self, time, icon, tempature):
		self.time = time
		self.icon = icon
		self.tempature = tempature

class WeatherInfo():
	def __init__(self, current = None, list = []):
		self.current = current
		self.list = list
	def set_current_weather(self, weather):
		self.current = weather
	def set_day_weather(self, weather):
		self.list = weather

class Weather(Service):
	def __init__(self, service_handler):

		self.service_handler = service_handler

		self.settings = get_settings()
		self.current_tempature = None
		self.current_rain = None
		self.current_humidity = None
		self.current_cloud = None
		self.forecast_weather_times = []
		self.weather = None

	def start_service(self):
		
		builder = self.service_handler.get_service('builder')

		self.current_tempature = builder.get_object("current-tempature")
		self.current_rain = builder.get_object("current-rain")
		self.current_humidity = builder.get_object("current-humidity")
		self.current_cloud = builder.get_object("current-cloud")
		self.forecast_weather_times = []
		self.weather = WeatherInfo()
		for i in range(8):
			time = builder.get_object(f"forecast-time{i + 1}")
			icon = builder.get_object(f"forecast-image{i + 1}")
			tempature = builder.get_object(f"forecast-tempature{i + 1}")
			self.forecast_weather_times.append(ForecastTime(time, icon, tempature))
		
		if(self.settings["modules"]["currentweather"]):
			self.set_current_weather()
			# update every 30 minutes
			GLib.timeout_add_seconds(1800, self.set_current_weather)
		else:
			builder.get_object("current-weather").hide()

		if(self.settings["modules"]["dayweather"]):
			self.set_day_weather()
			# update every 90 minutes.
			GLib.timeout_add_seconds(5400, self.set_day_weather)
		else:
			builder.get_object("forecast-weather").hide()
			
		if(self.settings["modules"]["currentweather"] == False and self.settings["modules"]["dayweather"] == False):
			builder.get_object("weather-container").hide()

	def set_current_weather(self):
		city_id = self.settings["cityid"]
		api_key = self.settings["openweatherkey"]
		try:
			result = requests.get(f"https://api.openweathermap.org/data/2.5/weather?units=imperial&id={city_id}&appid={api_key}")
			if(result.status_code == 200):
				result_json = result.json()
				self.current_tempature.set_text(str(round(result_json["main"]["temp"])) + "F")
				if("rain" in result_json):
					self.current_rain.set_text(str(result_json["rain"]["1h"]) + "mm")
				else:
					self.current_rain.set_text("0mm")
				self.current_humidity.set_text(str(result_json["main"]["humidity"]) + "%")
				self.current_cloud.set_text(str(result_json["clouds"]["all"]) + "%")
				self.weather.set_current_weather(result_json)
		except Exception as e:
			print("Problem with getting current weather: " + str(e))
		finally:
			return True

	def set_day_weather(self):
		city_id = self.settings["cityid"]
		api_key = self.settings["openweatherkey"]
		try:
			result = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?units=imperial&id={city_id}&appid={api_key}")
			if(result.status_code == 200):
				result_json = result.json()
				for i in range(8):
					weather = result_json["list"][i]
					time = datetime.datetime.fromtimestamp(weather["dt"])
					self.forecast_weather_times[i].time.set_text(time.strftime("%-I%p"))
					if(len(weather["weather"]) > 0):
						get_icon(f"https://openweathermap.org/img/wn/{weather['weather'][0]['icon']}.png", self.forecast_weather_times[i].icon)
					else:
						self.forecast_weather_times[i].icon.set_from_icon_name("gtk-missing-image")
					self.forecast_weather_times[i].tempature.set_text(str(round(weather["main"]["temp"])) + "F")
				self.weather.set_day_weather(result_json["list"][:8])
		except Exception as e:
			print("Problem with getting weather forcast: " + str(e))
		finally:
			return True
		
		
def get_icon(url, icon):
	def get_icon_from_thread(url,icon):
		try:
			res = requests.get(url, timeout=10)
			if(res.status_code == 200):
				loader = GdkPixbuf.PixbufLoader()
				loader.write(res.content)
				loader.close()
				pixbuf = loader.get_pixbuf()
				Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, icon.set_from_pixbuf, pixbuf)
			else:
				raise Exception("request did not return 200 " + res.text)
		except Exception as e:
			print(e)
			Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, icon.set_from_icon_name, "gtk-missing-image", Gtk.IconSize.MENU)

	thread = Thread(target=get_icon_from_thread, args=(url,icon))
	thread.start()

