import os
import glob
import struct
import datetime

import deepspeech
from audio_tools import VADAudio
import numpy as np
import pyaudio
from gi.repository import Gdk
from gi.repository import GLib
from threading import Thread

from pvporcupine import *

from espeakng import ESpeakNG

from utils.service_handler import Service
from utils.service_handler import ServiceHandler

class Voice(Thread, Service):

    def __init__(self, service_handler: ServiceHandler):
        super(Voice, self).__init__()

        self.service_handler = service_handler

        self._library_path = LIBRARY_PATH
        self._model_path = MODEL_PATH
        self._keyword_paths = [KEYWORD_PATHS["americano"]]
        self._sensitivities = [0.5]
        self.listening = True
        self.model = None
        self.porcupine = None
        self.pa = None
        self.audio_stream = None
        self.listener_icon = None
        self.listener_words = None

    def start_service(self):
        builder = self.service_handler.get_service('builder')

        self.screen_service = self.service_handler.get_service('screen')
        self.calendar_service = self.service_handler.get_service('calendar')
        self.snooze_service = self.service_handler.get_service('snooze')

        self.listener_icon = builder.get_object("listener-icon")
        self.listener_words = builder.get_object("listener-words")
        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.listener_icon.hide)
        Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.listener_words.hide)

        pbmm_model_name = glob.glob(os.path.join('*.pbmm'))
        tflite_model_name = glob.glob(os.path.join('*.tflite'))
        model_name = (pbmm_model_name + tflite_model_name)[0]
        self.model = deepspeech.Model(model_name)

        try:
            scorer_name = glob.glob(os.path.join('*.scorer'))[0]
            self.model.enableExternalScorer(scorer_name)
        except Exception as e:
            print(e)  

    def say(phrase):
        print(phrase)
        esng = ESpeakNG()
        esng.voice = "en+f4"
        esng.speed = 150
        esng.word_gap = 30
        # the k is because the start of the phrase is cut off
        esng.say("k " + phrase)

    def transcribe(self):
        # Start audio with VAD
        vad_audio = VADAudio(aggressiveness=1)
        print("Listening...")
        self.toggle_listener_icon()
        self.wake_screen()
        frames = vad_audio.vad_collector()
        # Stream from microphone to DeepSpeech using VAD
        stream_context = self.model.createStream()
        for frame in frames:
            if frame is not None:
                stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
            else:
                text = stream_context.finishStream()
                Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.listener_words.set_text, text)
                keep_listening = self.keyword_callback(text)
                if keep_listening is not True:
                    vad_audio.destroy()
                    return 1
                stream_context = self.model.createStream()
        vad_audio.destroy()
        stream_context.freeStream()
        return 1

    def set_listening(self, shouldListen):
        self.listening = shouldListen

    def toggle_listener_icon(self):
        is_visible = self.listener_icon.get_visible()
        if is_visible:
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.listener_words.set_text, "")
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.listener_words.hide)
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.listener_icon.hide)
        else:
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.listener_words.show)
            Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, self.listener_icon.show)
        

    def run(self):
        self.porcupine = Porcupine(
            library_path=self._library_path,
            model_path=self._model_path,
            keyword_paths=self._keyword_paths,
            sensitivities=self._sensitivities)

        self.pa = pyaudio.PyAudio()
        def get_audio_stream():
            return self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
            input_device_index=None)
        
        self.audio_stream = get_audio_stream()
        while self.listening:
            pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow = False)

            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

            result = self.porcupine.process(pcm)
            if result >= 0:
                print('Detected keyword')
                self.audio_stream.close()
                res = self.transcribe()
                if res:
                    self.toggle_listener_icon()
                    self.audio_stream = get_audio_stream()
        
        self.end_listener()
        return

    def end_listener(self):
        if(self.listening is False):
            if self.porcupine is not None:
                self.porcupine.delete()

            if self.audio_stream is not None:
                self.audio_stream.close()

            if self.pa is not None:
                self.pa.terminate()
        self.set_listening(False)

    def keyword_callback(self, text):
        print(text)
        if (self.snooze_service.is_checking_for_wakeup):
            if("yes" in text):
                self.snooze_service.end_check_for_wakeup()
            else:
                return True
        else:
            if("sleep" in text):
                self.screen_service.sleep_screen()
            elif("time" in text):
                self.say(datetime.datetime.now().strftime("%-I:%M%p"))
            elif("calendar" in text):
                self.calendar_service.set_calendar_to_display(text)
            elif("stop recording" in text):
                pass
            else:
                return True
