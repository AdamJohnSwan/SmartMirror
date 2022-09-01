from collections import namedtuple
import json
import os.path
import shutil
from typing import List

class Modules:
    clock: bool
    currentweather: bool
    dayweather: bool
    calendar: bool
    alarm: bool
    snooze: bool
    voice: bool

class AlarmSetting:
    Monday: str
    Tuesday: str
    Wednesday: str
    Thursday: str
    Friday: str
    Saturday: str
    Sunday: str

class SnoozeSetting:
    Monday: str
    Tuesday: str
    Wednesday: str
    Thursday: str
    Friday: str
    Saturday: str
    Sunday: str

class CalendarSettings:
    name: str
    group: str
    type: str
    url: str
    calendar_id: str
    credentials_path: str
    calendar_name: str
    username: str
    password: str

class Settings():
    cityid: int
    openweatherkey: str
    modules: Modules
    screentimeout: int
    alarm: AlarmSetting
    snooze: SnoozeSetting
    calendars: List[CalendarSettings]

def get_settings():
    file_exists = os.path.isfile("settings.json")
    if(file_exists is False):
        shutil.copyfile("settings.sample.json", "settings.json")
    with open("settings.json", "r") as settings:
        data = settings.read()
        json_data = json.loads(data)
        return json_data