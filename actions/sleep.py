from actions.settings import get_settings
from datetime import datetime
from datetime import time
from datetime import timedelta

class Interval():
    def __init__(self, start = 0, end = 0):
        self.start = start
        self.end = end

class Sleep():
    def __init__(self, builder, sleep_screen):
        self.settings = get_settings()
        self.is_checking_for_wakeup = False
        self.sleep_screen = sleep_screen
        self.sleep_times = self = [Interval()] * 7
        self.sleep_container = builder.get_object("sleep-container")
        if(self.settings["modules"]["sleep"]):
            self.translate_times(self.settings["sleep"])
    
    def translate_times(self, settings):
        def string_to_interval(string):
            split_times = string.split("-")
            start_string = split_times[0]
            end_string = split_times[1]
            start = datetime.strptime(start_string, "%H:%M:%S")
            end = datetime.strptime(end_string, "%H:%M:%S")
            start_seconds = ((start.hour * 60 * 60) + (start.minute * 60) + start.second)
            end_seconds = ((end.hour * 60 * 60) + (end.minute * 60) + end.second)
            return Interval(start_seconds, end_seconds)

        if (settings["Monday"]):
            self.sleep_times[0] = string_to_interval(settings["Monday"])
        if (settings["Tuesday"]):
            self.sleep_times[1] = string_to_interval(settings["Tuesday"])
        if (settings["Wednesday"]):
            self.sleep_times[2] = string_to_interval(settings["Wednesday"])
        if (settings["Thursday"]):
            self.sleep_times[3] = string_to_interval(settings["Thursday"])
        if (settings["Friday"]):
            self.sleep_times[4] = string_to_interval(settings["Friday"])
        if (settings["Saturday"]):
            self.sleep_times[5] = string_to_interval(settings["Saturday"])
        if (settings["Sunday"]):
            self.sleep_times[6] = string_to_interval(settings["Sunday"])

    def check_for_sleep(self):
        now = datetime.now()
        seconds = ((now.hour * 60 * 60) + (now.minute * 60) + now.second)
        sleep_time = self.sleep_times[now.weekday()]
        if (sleep_time.start > sleep_time.end):
            # start is greater than end which means that the end time is the next day.
            if (seconds < sleep_time.start and seconds > sleep_time.end):
                return
        else:
            if (seconds > sleep_time.start and seconds < sleep_time.end):
                return
        # if neither of these if-statements pass then the mirror is in sleep mode.
        self.check_for_wakeup()
    
    def check_for_wakeup(self):
        self.is_checking_for_wakeup = True
        # put a message on the screen prompting the user if they really want to wake up the mirror.

    def end_checking_for_wakeup(self):
        # user wants to turn on the mirror. Hide the prompt.
        self.is_checking_for_wakeup = False

        