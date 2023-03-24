from pythonosc import dispatcher, osc_server, osc_message_builder, udp_client
from DMMRead.DMMRead import Dmm
from threading import Thread
import googletrans
#from googletrans_new import google_tranlator
import random
import speech_recognition as sr
from TextKneter.speaker import Mixer, Speaker
from pydub.playback import play
import openai
import os
import pandas as pd
from openai.error import RateLimitError
from identities import ROLES

# That one is required to build local language models but needs PyTorch
#from easynmt import EasyNMT

# Try to load OpenAI API key from local Secrets folder
try:
    openai.api_key = pd.read_csv('Secrets\openAIKeyPeter.txt').columns[0]
except FileNotFoundError:
    # if not available: load dummy key to not break script execution:
    openai.api_key = '1234'

# GTP finetuning prompt - needed for custom AI response thread only
GTP_PROMPT_HEAD = ""


# ------------------------------------- global speech-to-text related variables ----------------

MAX_INTRA_PHRASE_PAUSE = 2.0
PHRASE_TIME_LIMIT = 20
# Instantiate Speech to text Recognizer
REC = sr.Recognizer()
REC.pause_threshold = MAX_INTRA_PHRASE_PAUSE

# Try Instantiating Microphone Connection:
try:
    micro = sr.Microphone()
    MIC = True
except OSError:
    micro = None
    MIC = False

# global variable to trigger interruption of listening
STOPLISTENING = None

# translator engine
STT_ENGINE = 'google'  # either "google" (online), or GPT
STT_LANG = 'de-DE' # language code of the language that is to be speech-to-text´ed

# --------- global electrometer (DMM) related variables ----------------

OPEN_PORTS = {}

# --------- global translation related variables ----------------

# language model:
# either "google" (online) or "facebook" (offlline) -> 'm2m_100_1.28M' model - facebook needs pytorch (required by EasyNMT)
TR_ENGINE = 'GPT'
TOKEN_CACHE = 1000

# --------- global text-to-speech related variables -------------

CH_NUM = 2
CURRENT_CH = 0

# ----------- GPT configuration -----------------

MAX_TOKENS = 40

# instantiate translator function (offline model might update/download ~ 3 gB)
if TR_ENGINE == 'google':
    trans_langs = list(googletrans.LANGCODES.values())
    translator = googletrans.Translator(service_urls=['translate.googleapis.com'])
    trans_func = lambda txt, src, trg: translator.translate(txt, src=src, dest=trg).text
elif TR_ENGINE == 'facebook':
    model = EasyNMT('m2m_100_1.2B')
    trans_langs = model.get_languages()
    trans_func = lambda txt, src, trg: model.translate(txt, source_lang=src, target_lang=trg)
elif TR_ENGINE == 'GPT':
    trans_langs = ['english', 'spanish', 'italian', 'russian', 'polish', 'greek', 'dutch', 'romanian', 'portuguese', 'arabic']
    #trans_langs = ['english', 'spanish', 'italian', 'russian', 'chinese']
    trans_prompt = lambda x,y,z: f'Translate from {x} to {y}:\n {z} => '
    def trans_func(txt, src, trg):
        global TOKEN_CACHE
        prompt = trans_prompt(src, trg, txt)
        tok_estimate = len([w for w in prompt.split(' ') if w != ' '])
        max_tokens = int(max(2040 - (TOKEN_CACHE + 10), 0))
        print(trans_prompt(src, trg, txt))
        result = openai.Completion.create(model="text-curie-001", prompt=trans_prompt(src, trg, txt),
                                           max_tokens=max_tokens, temperature=0.3, top_p=1.0, frequency_penalty=0.0,
                                           presence_penalty=0.0)
        TOKEN_CACHE = result['usage']['completion_tokens']
        result = result.choices[0].text.replace('\n', '')
        print(f'TK={TOKEN_CACHE}')
        return result

# ----------------- library of functions that can be triggered ------------------------------


def chainTransWorkFunc(txt, lang_list):
    txt_chain = [txt]
    if len(lang_list) == 2:
        txt_chain += [txt]
    else:
        for k in range(len(lang_list) - 1):
            txt_chain += [trans_func(txt=txt_chain[k], src=lang_list[k], trg=lang_list[k + 1])]
            # txt_chain += [translator.translate(txt_chain[k], src=lang_list[k], dest=lang_list[k+1]).text]
    result = []
    for k in range(len(txt_chain)):
        result += (lang_list[k],)
        result += (txt_chain[k],)
    return tuple(result)

def langSampler(txt, clen):
    source_l = 'de' if TR_ENGINE != 'GPT' else 'german'
    in_txt = txt
    chain_len = clen
    lang_list = [source_l]
    lang_sample = random.sample([k for k in range(len(trans_langs))], chain_len)
    for k in lang_sample:
        lang_list += [trans_langs[k]]
    lang_list += [source_l]
    return lang_list

def openDmmPort(unused_addr, args):
    """
    Opens a Serial USB port where the electrometer (DMM) Data is expected to stream in from:
    A Listener Thread is spawned to wait for incoming data in the background and send it through the
    udp client.

    :param args:
        Tuple - args[0] must be the Port adress string.
        For example "COM5" for windows port number 5
    """
    global OPEN_PORTS
    OPEN_PORTS[args[0]] = True
    dmm_thread = Thread(target=dmmThread, args=(args[0],), daemon=True)
    client.send_message("/portopened", args[0])
    dmm_thread.start()
    return

def closeDMMPort(unused_addr, args):
    """
    Closes a Serial USB port. (And makes it available for other processes again):

    :param args:
        Tuple - args[0] must be the Port adress string.
        For example "COM5" for windows port number 5
    """
    global OPEN_PORTS
    OPEN_PORTS[args[0]] = False
    client.send_message("/portclosed", args[0])
    return


def dmmThread(port):
    """
    Thread spawned by openDmmPort function.
    Sends electrometer meassurements with the osc tag "/dmm_COM5" (for port 5)
    through udp client
    """
    global OPEN_PORTS
    print(port)
    port_denied = True
    while port_denied:
        try:
            dmm = Dmm(port=port)
            port_denied = False
            client.send_message(f"/{port}_stream_start", "")
        except Exception:
            pass

    while OPEN_PORTS[port]:
        try:
            v = dmm.read().numericVal
            client.send_message(f"/dmm_{port}", str(v))
        except Exception:
            client.send_message(f"/{port}_stream_stop", "")
            OPEN_PORTS[port] = False
    dmm.close()
    return

def callback(recognizer, audio):
    try:
        if STT_ENGINE == 'google':
            data = REC.recognize_google(audio, language=STT_LANG)
        else:
            data = REC.recognize_sphinx(audio, language=STT_LANG)
    except sr.UnknownValueError:
        data = 'Nonn'
    except sr.RequestError:
        print('Google Trans Unavailable')
        data = REC.recognize_sphinx(audio, language=STT_LANG)
    if not data == 'Nonn':
        client.send_message("/STT", data)
    else:
        print('Silence')
    return


def calibrateThreshold(unused_addr, args):
    """
    Function triggered by "/calibrate" osc message - calibrates open MIC by setting
    background noise threshold
    """
    if not MIC:
        client.send_message("/calibration", "No Microphone")
        return

    client.send_message("/calibration", "Calibration commenced")
    try:
        with micro as source:
            REC.adjust_for_ambient_noise(source, duration=2.0)
            client.send_message("/calibration", f"Minimum threshold set to {REC.energy_threshold}")
    except (KeyboardInterrupt):
        print('Keyboard interrupt received.')
        pass


def startListening(unused_addr, args):
    """
    Function triggered by "/startlistening" osc message - starts background listening
    of microphone for spoken phrases to transform to text.
    """
    if not MIC:
        client.send_message("/startlistening", "No Microphone")
        return

    global STOPLISTENING
    client.send_message("/startlistening", "Listening thread started")
    STOPLISTENING = REC.listen_in_background(micro, callback, phrase_time_limit=PHRASE_TIME_LIMIT)
    return


def stopListening(unused_addr, args):
    """
    Function triggered by "/stoplistening" osc message - stops background listening
    of microphone
    """
    if not MIC:
        client.send_message("/stoppedlistening", "No Microphone")
        return

    global STOPLISTENING
    client.send_message("/stoppedlistening", "stopped microphone thread")
    STOPLISTENING(wait_for_stop=False)
    return


def chainTrans(unused_addrs, args):
    """
    Function triggered by "/chainTrans" osc message -
    Translates string args[0] through the languages indicated by a list of lang codes
    in args[1].
    """
    global TOKEN_CACHE
    TOKEN_CACHE = 1000
    lang_list = langSampler(args[0], args[1])
    thread_obj = Thread(target=chainTransThread, args=(args[0], lang_list,), daemon=True)
    thread_obj.start()
    return


def chainTransThread(txt, lang_list):
    """
    worker thread spawned by chainTrans to do the translation and send results through osc client with
    "/chainTransResult" tag.
    """
    result = chainTransWorkFunc(txt, lang_list)
    client.send_message('/chainTransResult', result)
    return


def tts(unused_addrs, args):
    """
    Text to Speech function
    """
    thread_obj = Thread(target=ttsThread, args=(args,), daemon=True)
    thread_obj.start()
    return


def ttsThread(args):
    """
    worker thread spawned by text-to-speech function
    """
    global CURRENT_CH
    CURRENT_CH = (CURRENT_CH + 1) % 10
    so = Speaker()
    tgt = f'spoken{CURRENT_CH}.mp3'
    so.speak(text=args[-1], target=tgt)
    #play(sound)
    client.send_message('/TTS', (CURRENT_CH,))
    return


def gpt(unused_addrs, msg, temp, freq, pres, tok, role, eng, trans):
    txt = ROLES[role] + msg
    thread_obj = Thread(target=gptThread, args=(txt, temp, freq, pres, tok, eng, trans), daemon=True)
    thread_obj.start()
    return

def gptThread(txt, temp, freq, pres, tok,eng, trans):
    global TOKEN_CACHE
    if tok < 0:
        tok = max(2040 - (TOKEN_CACHE + 10), 0)

    engine = ['ada',
              'babbage',
              'text-curie-001',
              'text-davinci-003']
    try:
        response = openai.Completion.create(engine=engine[eng], prompt=txt, temperature=temp, top_p=1,
                                            max_tokens=tok, frequency_penalty=freq, presence_penalty=pres)
        TOKEN_CACHE = response['usage']['completion_tokens']
        print('GPT_RESPONSE = ' + response.choices[0].text)
        if trans > 0:
            lang_list = langSampler(response.choices[0].text.replace('\n', ' '), trans)
            chain_end = chainTransWorkFunc(response.choices[0].text.replace('\n', ' '), lang_list)
            out = chain_end[-1]
        else:
            out = response.choices[0].text.replace('\n', ' ')
        client.send_message('/GPT', out)
    except RateLimitError:
        print('GPT funds depleted!')
        client.send_message('/GPT', txt)
    return


if __name__ == '__main__':
    ip = "127.0.0.1"
    sendPort = 7000
    inPort = 8000

    # sending osc messages on
    client = udp_client.SimpleUDPClient(ip, sendPort)

    # catching OSC messages
    dispatcher = dispatcher.Dispatcher()
    # register functionalities by mapping tgs to functions
    dispatcher.map("/calibrate", calibrateThreshold)
    dispatcher.map("/startlistening", startListening)
    dispatcher.map("/stoplistening", stopListening)
    dispatcher.map("/opendmmport", openDmmPort)
    dispatcher.map("/closeport", closeDMMPort)
    dispatcher.map("/chainTrans", chainTrans)
    dispatcher.map("/TTS", tts)
    dispatcher.map("/GPT", gpt)

    # server to listen to osc messages:
    server = osc_server.ThreadingOSCUDPServer((ip, inPort), dispatcher)
    print(f"serving on {server.server_address}")
    server.serve_forever()