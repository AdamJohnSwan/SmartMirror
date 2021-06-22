import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GdkPixbuf
from gi.repository import GLib
import datetime
import requests
from threading import Thread
from actions.settings import get_settings

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

class Weather():
	def __init__(self, builder):
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

		self.settings = get_settings()
		
		if(self.settings["modules"]["currentweather"]):
			self.set_current_weather()
		else:
			builder.get_object("current-weather").hide()
		if(self.settings["modules"]["dayweather"]):
			self.set_day_weather()
		else:
			builder.get_object("forecast-weather").hide()
		if(self.settings["modules"]["currentweather"] == False and self.settings["modules"]["dayweather"] == False):
			builder.get_object("weather-container").hide()
	def set_current_weather(self):
		city_id = self.settings["cityid"]
		api_key = self.settings["openweatherkey"]
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
		# update every 30 minutes
		GLib.timeout_add_seconds(1800, self.set_current_weather)
	def set_day_weather(self):
		city_id = self.settings["cityid"]
		api_key = self.settings["openweatherkey"]
		first_time = datetime.datetime.now()
		result = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?units=imperial&id={city_id}&appid={api_key}")
		if(result.status_code == 200):
			result_json = result.json()
			for i in range(8):
				weather = result_json["list"][i]
				time = datetime.datetime.fromtimestamp(weather["dt"])
				if(i == 0):
					first_time = time
				self.forecast_weather_times[i].time.set_text(time.strftime("%-I%p"))
				if(len(weather["weather"]) > 0):
					get_icon(f"https://openweathermap.org/img/wn/{weather['weather'][0]['icon']}.png", self.forecast_weather_times[i].icon)
				else:
					self.forecast_weather_times[i].icon.set_from_icon_name("gtk-missing-image")
				self.forecast_weather_times[i].tempature.set_text(str(round(weather["main"]["temp"])) + "F")
			self.weather.set_day_weather(result_json["list"][:8])
		difference = (first_time + datetime.timedelta(hours = 3)) - datetime.datetime.now()
		time_to_check_again =  round(difference.total_seconds())
		GLib.timeout_add_seconds(time_to_check_again, self.set_day_weather)
		
def get_icon(url, icon):
	def callback(res, *args, **kwargs):
		loader = GdkPixbuf.PixbufLoader()
		loader.write(res.content)
		loader.close()
		icon.set_from_pixbuf(loader.get_pixbuf())
	kwargs = {}
	kwargs['hooks'] = {'response': callback}
	kwargs['timeout'] = 15
	thread = Thread(target=requests.get, args=[url], kwargs=kwargs)
	thread.start()