from utils.settings import get_settings
from datetime import datetime
from gi.repository import GLib
from utils.service import Service


class Interval():
    def __init__(self, start = 0, end = 0):
        self.start = start
        self.end = end

class Snooze(Service):
    def __init__(self, service_handler):
        self.service_handler = service_handler
        self.screen_service = None
        self.settings = get_settings()
        self.is_checking_for_wakeup = False
        self.snooze_times = []
        self.wrapper = None

        self.content = None
        self.message = None

    def start_service(self):
        builder = self.service_handler.get_service('builder')
        self.stack = builder.get_object("stack")

        self.screen_service = self.service_handler.get_service('screen')

        self.snooze_times = [Interval()] * 7

        children = self.stack.get_children()
        # for some reason set_visible_child_by_name does not work so the child objects have to be retrieved here for use in hiding/showing the prompt.
        for child in children:
            name = child.get_name()
            if (name == "weather-calendar-content"):
                self.content = child
                self.stack.set_visible_child(self.content)
            elif (name == "snooze-container"):
                self.message = child

        if(self.settings["modules"]["snooze"]):
            self.translate_times(self.settings["snooze"])
    
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
            self.snooze_times[0] = string_to_interval(settings["Monday"])
        if (settings["Tuesday"]):
            self.snooze_times[1] = string_to_interval(settings["Tuesday"])
        if (settings["Wednesday"]):
            self.snooze_times[2] = string_to_interval(settings["Wednesday"])
        if (settings["Thursday"]):
            self.snooze_times[3] = string_to_interval(settings["Thursday"])
        if (settings["Friday"]):
            self.snooze_times[4] = string_to_interval(settings["Friday"])
        if (settings["Saturday"]):
            self.snooze_times[5] = string_to_interval(settings["Saturday"])
        if (settings["Sunday"]):
            self.snooze_times[6] = string_to_interval(settings["Sunday"])

    def check_for_snooze(self):
        import pdb; pdb.set_trace()
        now = datetime.now()
        seconds = ((now.hour * 60 * 60) + (now.minute * 60) + now.second)
        snooze_time = self.snooze_times[now.weekday()]
        if (snooze_time.start > snooze_time.end):
            # start is greater than end which means that the end time is the next day.
            if (seconds < snooze_time.start and seconds > snooze_time.end):
                return
        else:
            if (seconds > snooze_time.start and seconds < snooze_time.end):
                return
        # if neither of these if-statements pass then the mirror is in snooze mode.
        self.check_for_wakeup()
    
    def check_for_wakeup(self):
        self.is_checking_for_wakeup = True
        # put a message on the screen prompting the user if they really want to wake up the mirror.
        if (self.message != None):
            self.stack.set_visible_child(self.message)
            GLib.timeout_add_seconds(60, self.check_for_wakeup_timeout)
        

    def check_for_wakeup_timeout(self):
        if self.is_checking_for_wakeup:
            self.screen_service.sleep_screen()
            if (self.content != None):
                self.stack.set_visible_child(self.content)

    def end_check_for_wakeup(self):
        self.is_checking_for_wakeup = False
        # user wants to turn on the mirror. Hide the prompt.
        if (self.content != None):
            self.stack.set_visible_child(self.content)


        