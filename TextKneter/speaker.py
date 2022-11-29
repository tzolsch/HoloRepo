from gtts import gTTS
import gtts
import os


from typing import Optional, Union, Tuple, Sequence, Callable, List
from typing_extensions import Literal
from pydub import AudioSegment
from pydub.playback import play
from subprocess import Popen
import time

SPEAKER_LANGS = list(gtts.lang.tts_langs().keys())
#TEMP = "D:\PyStuff\TDModules\data_temp"
TEMP = "C:\HoloData\HoloSecrets\speaker_temp"


class Mixer:
    sub_channel = 0
    def __init__(
            self,
            w_dir: str = TEMP,
    ):
        self.w_dir: str = w_dir
        self.audio = None
        self._sub_channel = os.path.join(w_dir, f"mx{Mixer.sub_channel}")
        Mixer.sub_channel += 1

    def load(self, source):
        if isinstance(source, str):
            p = os.path.join(self.w_dir, source)
            self.audio = AudioSegment.from_mp3(p)
        else:
            self.audio = source

    def mixin(self, source, mix_lag=0, ):
        if isinstance(source, str):
            p = os.path.join(self.w_dir, source)
            source = AudioSegment.from_mp3(p)

        if self.audio is None:
            self.audio = source
        else:
            if 0 <= mix_lag < 1:
                m_lag = len(self.audio) * mix_lag
            elif mix_lag < 0:
                m_lag = max(len(self.audio) + mix_lag, 0)
            dubbed_sound = self.audio.overlay(source, position=m_lag)
            self.audio = dubbed_sound + source[len(dubbed_sound) - m_lag:]

    def play(self):
        play(self.audio)

    def sub_play(self):
        self.audio.export(self._sub_channel, format='wav')
        p = Popen(["aplay", self._sub_channel])
        return p

    def write(self, target):
        target = os.path.join(self.w_dir, target)


class Speaker:
    sp_global = 0

    def __init__(
        self,
        engine: Literal["gTTS", "pyttsx"] = "gTTS",
        language: str = "de",
        engine_kwargs: dict = {},
        w_dir: str = TEMP,
        channel: Optional[int] = None,
    ):
        if channel is None:
            Speaker.sp_global += 1
            channel = Speaker.sp_global

        self.engine = engine
        self.engine_kwargs = engine_kwargs
        self.channel = channel
        self.engine_kwargs.update({"lang": language})
        self.w_dir = w_dir
        self._temp_pointer = os.path.join(self.w_dir, f"spoken_temp_{self.channel}.mp3")

    def speak(
        self,
        text: Optional[str] = None,
        target: Optional[str] = None,
        **kwargs,
    ):

        if target is not None:
            target = os.path.join(self.w_dir, target)

        in_kwargs = self.engine_kwargs
        in_kwargs.update(kwargs)

        text_obj = gTTS(text, **self.engine_kwargs)
        speak_to = target or self._temp_pointer
        text_obj.save(speak_to)
        print(speak_to)
        time.sleep(2)
        sound = AudioSegment.from_mp3(speak_to)
        return sound


if __name__ == "__main__":
    so = Speaker()
    mx = Mixer()
    h=so.speak('Hallo Welt.')
    mx.load(h)
    mx.mixin(h, .5)
    mx.play()
