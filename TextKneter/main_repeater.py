import speaker
import kneter
from kneter import translation_chain
from pydub import AudioSegment
from random import randint


def chain_echo(txt, mix_lag=.75, fade_delta=-2, steps=5, start_mixin=False, final_mixin=True):
    
    stereo_func = lambda x: x if x != 0 else -100
    speak = speaker.Speaker()
    mixer = speaker.Mixer()
    fade = 0
    available_langs = list(set(kneter.KNETER_LANGS) & set(speaker.SPEAKER_LANGS))
    chain = [available_langs[randint(0, len(available_langs)-1)] for k in range(steps)]
    spoken = [AudioSegment.silent(duration=1)] * len(chain)
    chain = chain + ['de']
    start = speak.speak(text=txt, lang='de')
    txt = translation_chain(txt, ['de', chain[0]])
    stereo_channel = 0
    for l in range(len(spoken)):
        spoken[l] = speak.speak(text=txt, lang=chain[l]).apply_gain_stereo(stereo_func(fade*(stereo_channel%2)), stereo_func(fade*((stereo_channel+1)%2)))
        stereo_channel += 1
        #spoken[l] = speak.speak(text=txt, lang=chain[l]).apply_gain(fade)
        #print(f'language = {chain[l]}')
        #print(f'text = {txt}')
        txt = translation_chain(txt, [chain[l], chain[l + 1]])
        fade = fade + fade_delta

    final = speak.speak(text=txt, lang='de')
    if start_mixin:
        mixer.load(start)
    else:
        mixer.load(AudioSegment.silent(duration=1))
    for s in spoken:
        mixer.mixin(s, mix_lag=mix_lag)
    if final_mixin:
        mixer.mixin(final, mix_lag=-5000)
    return mixer, txt

def looper(func, loops=5, **kwargs):
    p = None
    for k in range(0, loops):
        mixer, txt = func(**kwargs)
        if p is None:
            p = mixer.sub_play()
        else:
            p.wait()
            p = mixer.sub_play()




if __name__ == "__main__":
    #print('go')
    #listen = listener.LiveListener(duration=10, language="de-DE")
    #txt = listen.listen()
    #print(txt)

    txt = 'hallo.'

    looper(chain_echo, loops=5, steps=5, mix_lag=.7, txt=txt)
