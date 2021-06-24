import os
import glob
import struct
from threading import Thread

import deepspeech
from audio_tools import VADAudio
import numpy as np
import pyaudio

from pvporcupine import *

class KeywordListener(Thread):

    def __init__(self, builder, keyword_callback, wake_screen):
        super(KeywordListener, self).__init__()

        self._library_path = LIBRARY_PATH
        self._model_path = MODEL_PATH
        self._keyword_paths = [KEYWORD_PATHS["americano"]]
        self._sensitivities = [0.5]
        self.listening = True
        self.listener_icon = builder.get_object("listener-icon")
        self.listener_words = builder.get_object("listener-words")
        self.listener_icon.hide()
        self.listener_words.hide()
        self.keyword_callback = keyword_callback
        self.wake_screen = wake_screen

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
        vad_audio = VADAudio(aggressiveness=1)
        print("Listening (ctrl-C to exit)...")
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
                self.listener_words.set_text(text)
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
            self.listener_words.set_text("")
            self.listener_words.hide()
            self.listener_icon.hide()
        else:
            self.listener_words.show()
            self.listener_icon.show()
        

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
            pcm = self.audio_stream.read(self.porcupine.frame_length)

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
