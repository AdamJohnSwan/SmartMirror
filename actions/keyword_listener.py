import os
import glob
import struct

import multiprocessing
import deepspeech
from audio_tools import VADAudio
import numpy as np
import pyaudio

from pvporcupine import *
from actions.speech import say, say_time

class KeywordListener():

    def __init__(self):

        self._library_path = LIBRARY_PATH
        self._model_path = MODEL_PATH
        self._keyword_paths = [KEYWORD_PATHS["americano"]]
        self._sensitivities = [0.5]
        self.listening = True
        self.tasks = None

        model_name = glob.glob(os.path.join('*.pbmm'))[0]
        self.model = deepspeech.Model(model_name)

        self.porcupine = None
        self.pa = None
        self.audio_stream = None

        try:
            scorer_name = glob.glob(os.path.join('*.scorer'))[0]
            self.model.enableExternalScorer(scorer_name)
        except Exception as e:
            print(e)        

    def transcribe(self):
        # Start audio with VAD
        vad_audio = VADAudio(aggressiveness=1,
                             device=None,
                             input_rate=16000,
                             file=None)
        print("Listening (ctrl-C to exit)...")
        self.tasks.put({"task":"toggle_listener_icon"})
        self.tasks.put({"task":"wake_screen"})
        frames = vad_audio.vad_collector()
        # Stream from microphone to DeepSpeech using VAD
        stream_context = self.model.createStream()
        for frame in frames:
            if frame is not None:
                stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
            else:
                text = stream_context.finishStream()
                print(text)
                self.tasks.put({"task": "set_listener_text", "args": text})
                keep_listening = self.check_keyword(text)
                if keep_listening is not True:
                    vad_audio.destroy()
                    return 1
                stream_context = self.model.createStream()        
        vad_audio.destroy()
        return 1

    def check_keyword(self, text):
        if("wake" in text):
            self.tasks.put({"task": "wake_screen"})
        elif("sleep" in text):
            self.tasks.put({"task": "sleep_screen"})
        elif("time" in text):
            say_time()
        elif("stop recording" in text):
            pass
        else:
            return True

    def set_listening(self, shouldListen):
        self.listening = shouldListen

    def run(self, tasks):
        self.tasks = tasks
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
            pcm = self.audio_stream.read(self.porcupine.frame_length)

            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

            result = self.porcupine.process(pcm)
            if result >= 0:
                print('Detected keyword')
                self.audio_stream.close()
                res = self.transcribe()                   
                if res:
                    self.tasks.put({"task":"toggle_listener_icon"})
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
