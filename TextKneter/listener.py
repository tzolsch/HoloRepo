import nltk
import numpy as np
import pandas as pd
import speech_recognition as sr

from typing import Optional, Union, Tuple, Sequence, Callable
from typing_extensions import Literal

LISTENER_LANGS = {"de": "de-DE", "en": "en-US"}


class LiveListener:
    def __init__(
        self,
        language: str = "de-DE",
        duration: Union[int, str] = 5,
        engine: Literal[
            "recognize_google",
            "recognize_google_cloud",
            "recognize_bing",
            "recognize_houndify",
            "recognize_ibm",
            "recognize_wit",
            "recognize_sphinx",
        ] = "recognize_google",
        engine_kwargs: dict = {},
    ):
        self.listener = sr.Recognizer()
        self.duration = duration
        self.lang = language
        self.engine = engine
        self.source_accessor = getattr(sr, "Microphone")()
        self.engine_kwargs = engine_kwargs

    def listen(self, duration: Optional[int] = None):

        duration = duration or self.duration
        with self.source_accessor as source:
            audio_data = self.listener.record(source, duration=duration)
            text = getattr(self.listener, self.engine)(
                audio_data, language=self.lang, **self.engine_kwargs
            )
            return text


if __name__ == "__main__":
    L1 = LiveListener(duration=20, language="de-DE")
    a = L1.listen()
    print(a)
