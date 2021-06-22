import json
import os.path
import shutil

def get_settings():
    file_exists = os.path.isfile("settings.json")
    if(file_exists is False):
        shutil.copyfile("settings.sample.json", "settings.json")
    with open("settings.json", "r") as settings:
        data = settings.read()
        return json.loads(data)