from espeakng import ESpeakNG

def say(phrase):
    print(phrase)
    esng = ESpeakNG()
    esng.voice = "en-us"
    esng.pitch = 40
    esng.speed = 50
    esng.volume = 200
    esng.voices
    esng.say(phrase)

