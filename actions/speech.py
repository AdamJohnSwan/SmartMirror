from espeakng import ESpeakNG

def say(phrase):
    print(phrase)
    esng = ESpeakNG()
    esng.voice = "en+f4"
    esng.speed = 150
    esng.word_gap = 30
    # the k is because the start of the phrase is cut off
    esng.say("k " + phrase)
