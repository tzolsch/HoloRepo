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
from easynmt import EasyNMT


openai.api_key = pd.read_csv('Secrets\openAIKeyPeter.txt').columns[0]

GPT_prompt_head = "1. Erkenne dich selbst. " \
         "2. Beherrsche die Regeln deiner Hexenkunst. " \
         "3. Höre nie auf zu lernen. " \
         "4. Wende dein Wissen weise an. " \
         "5. Lebe im Gleichgewicht. " \
         "6. Wisse immer, was du sagst und warum du es sagst. " \
         "7. Sei mental konzentriert. " \
         "8. Lebe im Einklang mit der Natur. " \
         "9. Feiere das Leben. " \
         "10. Atme bewusst, ernähre dich gesund. " \
         "11. Trainiere deinen Körper. " \
         "12. Meditiere. " \
         "13. Ehre die Göttin und den Gott. "


r = sr.Recognizer()
try:
    m = sr.Microphone()
    Mic = True
except OSError:
    m = None
    Mic = False

stopListening = None
open_ports = {}

STT_ENGINE = 'google'  # either "google" (online), or "sphinx" (offline) ("sphinx" is fallback engine) - sphinx not implemented yet
STT_LANG = 'de-DE'

#TR_ENGINE = 'facebook'
TR_ENGINE = 'google'# either "google" (online) or "facebook" (offlline) -> 'm2m_100_1.28M' model)
if TR_ENGINE == 'google':
    trans_langs = list(googletrans.LANGCODES.values())
    translator = googletrans.Translator(service_urls=['translate.googleapis.com'])
    trans_func = lambda txt, src, trg: translator.translate(txt, src=src, dest=trg).text
elif TR_ENGINE == 'facebook':
    model = EasyNMT('m2m_100_1.2B')
    trans_langs = model.get_languages()
    trans_func = lambda txt, src, trg: model.translate(txt, source_lang=src, target_lang=trg)


def dmmThread(port):
    global open_ports
    print(port)
    port_denied = True
    while port_denied:
        try:
            dmm = Dmm(port=port)
            port_denied = False
            client.send_message(f"/{port}_stream_start", "")
        except Exception:
            pass

    while open_ports[port]:
        try:
            v = dmm.read().numericVal
            client.send_message(f"/dmm_{port}", str(v))
        except Exception:
            client.send_message(f"/{port}_stream_stop", "")
            open_ports[port] = False
    dmm.close()
    return


def openDmmPort(unused_addr, args):
    global open_ports
    open_ports[args[0]] = True
    dmm_thread = Thread(target=dmmThread, args=(args[0],), daemon=True)
    client.send_message("/portopened", args[0])
    dmm_thread.start()
    return


def closeDMMPort(unused_addr, args):
    global open_ports
    open_ports[args[0]] = False
    client.send_message("/portclosed", args[0])
    return


def callback(recognizer, audio):
    try:
        if STT_ENGINE == 'google':
            data = r.recognize_google(audio, language=STT_LANG)
        else:
            data = r.recognize_sphinx(audio, language=STT_LANG)
    except sr.UnknownValueError:
        print('hum?')
        data = 'hum?'
    except sr.RequestError:
        print('Google Trans Unavailable')
        data = r.recognize_sphinx(audio, language=STT_LANG)
    client.send_message("/STT", data)
    return


def calibrateThreshold(unused_addr, args):

    if not Mic:
        client.send_message("/calibration", "No Microphone")
        return

    client.send_message("/calibration", "Calibration commenced")
    try:
        with m as source:
            r.adjust_for_ambient_noise(source, duration=2.0)
            client.send_message("/calibration", f"Minimum threshold set to {r.energy_threshold}")
    except (KeyboardInterrupt):
        print('Keyboard interrupt received.')
        pass


def startListening(unused_addr, args):
    if not Mic:
        client.send_message("/startlistening", "No Microphone")
        return

    global stopListening
    client.send_message("/startlistening", "Listening thread started")
    stopListening = r.listen_in_background(m, callback, phrase_time_limit=10)
    return


def stopListening(unused_addr, args):
    if not Mic:
        client.send_message("/stoppedlistening", "No Microphone")
        return

    global stopListening
    client.send_message("/stoppedlistening", "stopped microphone thread")
    stopListening(wait_for_stop=False)
    return


def chainTrans(unused_addrs, args):
    in_txt = args[0]
    chain_len = args[1]
    lang_list = ['de']
    lang_sample = random.sample([k for k in range(len(trans_langs))], chain_len)
    for k in lang_sample:
        lang_list += [trans_langs[k]]
    lang_list += ['de']
    thread_obj = Thread(target=chainTransThread, args=(in_txt, lang_list,), daemon=True)
    thread_obj.start()
    return


def chainTransThread(txt, lang_list):
    txt_chain = [txt]
    if len(lang_list) == 2:
        txt_chain += [txt]
    else:
        for k in range(len(lang_list) - 1):
            txt_chain += [trans_func(txt=txt_chain[k], src=lang_list[k], trg=lang_list[k+1])]
            # txt_chain += [translator.translate(txt_chain[k], src=lang_list[k], dest=lang_list[k+1]).text]
    result = []
    for k in range(len(txt_chain)):
        result += (lang_list[k],)
        result += (txt_chain[k],)
    result = tuple(result)
    client.send_message('/chainTransResult', result)
    return


def tts(unused_addrs, args):
    thread_obj = Thread(target=ttsThread, args=(args,), daemon=True)
    thread_obj.start()
    return


def ttsThread(args):
    so = Speaker()
    tgt = None
    sound = so.speak(text=args[-1], target=tgt)
    play(sound)
    #client.send_message('/TTS', os.path.join(so.w_dir, tgt))
    return


def gpt(unused_addrs, args):
    txt = GPT_prompt_head + args
    print('GPT triggered!')
    thread_obj = Thread(target=gptThread, args=(txt,), daemon=True)
    thread_obj.start()
    return


def gptThread(args):
    response = openai.Completion.create(engine="text-curie-001",prompt=args,temperature=0.6,top_p=1,max_tokens=20,frequency_penalty=0,presence_penalty=0)
    print('GPT_PROMPT = ' + args)
    print('GPT_RESPONSE = ' + response.choices[0].text)
    client.send_message('/GPT',response.choices[0].text.replace('\n', ' '))
    return


if __name__ == '__main__':
    ip = "127.0.0.1"
    sendPort = 7000
    inPort = 8000

    # sending osc messages on
    client = udp_client.SimpleUDPClient(ip, sendPort)

    # catching OSC messages
    dispatcher = dispatcher.Dispatcher()
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