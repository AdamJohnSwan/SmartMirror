from espeakng import ESpeakNG
import datetime

def say(phrase):
    print(phrase)
    esng = ESpeakNG()
    esng.voice = "en-us"
    esng.pitch = 40
    esng.speed = 50
    esng.volume = 200
    esng.voices
    esng.say(phrase)

def say_time():
    esng = ESpeakNG()
    esng.voice = "en-us"
    esng.pitch = 40
    esng.speed = 50
    esng.volume = 200
    esng.voices
    esng.say(datetime.datetime.now().strftime("%-I:%-M%p"))

