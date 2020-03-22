import io
import os

import sounddevice as sd

from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from scipy.io.wavfile import write
from pydub import AudioSegment
from pywebostv.discovery import *
from pywebostv.connection import *
from pywebostv.controls import *


def get_audio_file_name():
    file_name = os.path.join(
        os.path.dirname(__file__),
        'resources',
        'audio.raw')

    return file_name


def record_audio(file_name, fs):
    seconds = 5

    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    print('recording')
    sd.wait()
    print('finish')
    write(file_name, fs, audio) 


def get_audio_content(file_name):
    with io.open(file_name, 'rb') as audio_file:
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    return audio


def wav_to_flac(file_name):
    wav_audio = AudioSegment.from_file(file_name, format='wav')
    wav_audio.export(file_name, format='flac')


def classify_and_exec(sysctrl, appctrl, mediactrl, msg):

    if 'netflix' in msg:
        apps = appctrl.list_apps()
        netflix = [x for x in apps if "netflix" in x["title"].lower()][0]
        appctrl.launch(netflix)

    elif 'volume' in msg:
        volume = mediactrl.get_volume()['volume']

        if 'aumentar' in msg:
            new_volume = volume + 15 if volume <= 85 else 100

        elif 'diminuir' in msg:
            new_volume = volume - 15 if volume >= 15 else 0

        mediactrl.set_volume(new_volume)

    elif 'desligar tv' in msg:
        sysctrl.power_off()

    elif 'mensagem' in msg:
        sysctrl.notify(msg.replace('mensagem', ''))


def run(stt_client, stt_config, fs, sysctrl, appctrl, mediactrl):
    file_name = get_audio_file_name()
    
    while True:
        record_audio(file_name, fs)
        wav_to_flac(file_name)
        audio = get_audio_content(file_name)
        
        response = stt_client.recognize(stt_config, audio)
        if response.results:
            result = response.results[0].alternatives[0].transcript
            classify_and_exec(sysctrl, appctrl, mediactrl, result.lower())


if __name__ == '__main__':
    store = {}
    tv_client = WebOSClient.discover()[0]
    tv_client.connect()

    for status in tv_client.register(store):
        if status == WebOSClient.PROMPTED:
            print("Please accept the connect on the TV!")
        elif status == WebOSClient.REGISTERED:
            print("Registration successful!")

            sysctrl = SystemControl(tv_client)
            appctrl = ApplicationControl(tv_client)
            mediactrl = MediaControl(tv_client)

            fs = 16000

            stt_client = speech.SpeechClient()
            stt_config = types.RecognitionConfig(
                encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
                sample_rate_hertz=fs,
                language_code='pt-BR')
 
            run(stt_client, stt_config, fs, sysctrl, appctrl, mediactrl)

