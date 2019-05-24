import os
import re
from pydub import AudioSegment
import speech_recognition as sr


__all__ = ['transcribe']


def transcribe(file_path):
    print('file_path', file_path)
    old_audio_file = AudioSegment.from_file(file_path, format='m4a')
    new_audio_file_path = file_path[:-3] + 'wav'
    old_audio_file.export(new_audio_file_path, format='wav')
    print('new_audio_file_path', new_audio_file_path)

    r = sr.Recognizer()
    with sr.AudioFile(new_audio_file_path) as source:
        audio = r.record(source)
        os.remove(new_audio_file_path)

    try:
        text = r.recognize_google(audio, language='zh-TW')
    except (sr.UnknownValueError, sr.RequestError) as e:
        text = "{0}".format(e)

    return text


# if __name__ == '__main__':
#     file_path_ = os.path.join(os.path.dirname(__file__), '..', 'static', 'tmp', 'tmp2vh4owtp.m4a')
#
#     print(transcribe(file_path_))
