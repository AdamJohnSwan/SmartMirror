import datetime
import time
import pyaudio
import wave
from utils.service import Service
from utils.settings import get_settings
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

class Alarm(Service):

    def __init__(self, service_handler):
        self.service_handler = service_handler
        self.settings = get_settings()
        self.sleep_timer = datetime.datetime.now() + datetime.timedelta(minutes=self.settings["screentimeout"])
        self.is_awake = True
        self.wake_up_times = {}
        # set this to true so the alarm does not trigger at first startup.
        self.alarm_triggered = True
        self.alarm_stream = None
        self.alarm_enabled = False
        self.pa = None
        self.service_started = False

    def start_service(self):
        self.screen_service = self.service_handler.get_service('screen')
        builder = self.service_handler.get_service('builder')
        self.alarm_icon = builder.get_object("alarm")
        if(self.settings["modules"]["alarm"]):
            self.wake_up_times = self.get_wake_up_times()
            self.alarm_enabled = True
            self.set_alarm(True)
            if("soundfile" in self.settings["alarm"]):
                self.sound_file = self.settings["alarm"]["soundfile"]
        else:
            self.set_alarm(False)
        self.service_started = True
    
    def get_wake_up_times(self):
        if (self.service_started):
            return self.wake_up_times
        else:
            try:
                self.wake_up_times = self.settings["alarm"]
                return self.wake_up_times
            except ValueError:
                print("alarm module is set but no alarm settings exist")

    def check_alarm(self):
        now = datetime.datetime.now()
        try:
            wake_up_time = self.get_wake_up_times()[now.strftime("%A")]
            if(wake_up_time != False):
                parsed_time = datetime.datetime.strptime(wake_up_time, "%H:%M:%S").replace(year=now.year, month=now.month, day=now.day)
                if(now > parsed_time and self.alarm_enabled):
                    if (self.alarm_triggered == False):
                        self.screen_service.wake_screen()
                        self.alarm_triggered = True
                        self.play_alarm()
                else:
                    self.alarm_triggered = False
        except KeyError as e:
            # Either the alarm for the day doesn't exist, or the time is in the wrong format.
            print("Cannot find alarm time for today: " + str(e))
        except ValueError as e:
            # Either the alarm for the day doesn't exist, or the time is in the wrong format.
            print("Cannot parse time: " + str(e))
    
    def play_alarm(self):
        if(self.sound_file == None):
            return
        start = time.time()
        ten_minutes_in_seconds = 600
        try:
            wf = wave.open(self.sound_file, 'rb')
            def callback(in_data, frame_count, time_info, status):
                data = wf.readframes(frame_count)
                if(time.time() - start > ten_minutes_in_seconds):
                    return(data, pyaudio.paComplete)
                else:
                    if(len(data) < frame_count):
                        wf.rewind()
                    return (data, pyaudio.paContinue)

            pa = pyaudio.PyAudio()

            self.alarm_stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True,
                            stream_callback=callback)

            self.pa = pa

            GLib.timeout_add_seconds(ten_minutes_in_seconds, self.stop_alarm)
        except Exception as e:
            print(f"Error running alarm tone: {str(e)}")
            self.stop_alarm()
    
    def stop_alarm(self):
        if(self.alarm_stream != None):
            self.alarm_stream.close()
        if(self.pa != None):
            self.pa.terminate()
        # function is called by Glib.timeout_add. Return false so the function is not called again.
        return False
    
    def set_alarm(self, enabled = None):
        if(enabled == None):
            enabled = not self.alarm_enabled

        if(enabled):
            # set this to true so the alarm does not start as soon as it is enabled.
            self.alarm_triggered = True
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.alarm_icon.show)
        else:
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.alarm_icon.hide)

        self.alarm_enabled = enabled
    