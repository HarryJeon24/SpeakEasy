import json
import os.path
import pickle
import time
from typing import Dict, Any, List
import requests
from emora_stdm import DialogueFlow, Macro, Ngrams
import re
import pyaudio
import wave
import openai
from gtts import gTTS
from src.utils import MacroGPTJSON, MacroNLG
from enum import Enum


class V(Enum):
    objective = 0,  # str cut, color, perm, error
    appointment_hours = 1  # str yes, no


transitions = {
    'state': 'start',
    '`Hello. How are you?` #SET($RESPONSE="Hello. How are you?") #GTTS #USERINPUT': {
        '[good]': {
            '`Glad to hear that you are doing well :)`': {
                'error': {
                    '`See you later!`': 'feedback'
                }
            }
        },
        'error': {
            '`I hope your day gets better soon :(`': {
                'error': {
                    '`Take care!`': 'feedback'
                }
            }
        }
    }
}

transitions_feedback = {
    'state': 'feedback',
    '`Congratulation! The evaluation process is over. Based on the conversation we just had, here are some '
    'suggestions.` #SET($RESPONSE="Congratulation! The evaluation process is over. Based on the conversation we just '
    'had, here are some suggestions.") #GTTS $RESPONSE=#QUEST #GTTS $RESPONSE=#SPEED #GTTS'
    '$RESPONSE=#TIC #GTTS $RESPONSE=#ACKNOW #GTTS $RESPONSE=#ACKWARD #GTTS #USERINPUT': {
        '#SET($NATEX="yes great wonderful fantastic excellent happy glad perfect awesome thank") #SIMPLENATEX': {
            '`My pleasure.` #SET($RESPONSE="My pleasure") #GTTS': 'evaluation',
        },
        'error': {
            '`I am sorry.` #SET($RESPONSE="I am sorry.") #GTTS': 'evaluation'
        }
    }
}
transitions_evaluation = {
    'state': 'evaluation',
    '`Now could you do a evaluation for me? How was my overall behavior? Was I coherent? Was I smart enough to make good conversation with you? Would you consider make feedback seriously? You will get a longer time to answer it. So do not worry about the time constraint.` #SET($RESPONSE="Now could you do a evaluation of me? How was my overall behavior?") #GTTS #USERINPUT': {
        '#GPTEVAL': {
            '`Thank you for your feedback.`': 'end'
        },
        'error': {
            '`Sorry, I did not understand it.`': 'end'
        }
    }
}


class MacroNatex(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if vars["CURRENT"] in vars["NATEX"]:
            return True
        else:
            return False


class MacrogTTS(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        tts = gTTS(text=vars['RESPONSE'], lang='en')
        tts.save("bot_output.mp3")
        os.system("start bot_output.mp3")
        time.sleep(7)
        return True


class MacroNumQuestions(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'ANSWERS' not in vars:
            vars['NUMQUEST'] = 0
        else:
            vars['NUMQUEST'] = vars['ANSWERS'].count("?")
        if vars['NUMQUEST'] < 5:
            vars['QUESTFEEDBACK'] = "You should ask more questions."
        else:
            vars['QUESTFEEDBACK'] = "You have asked enough questions."
        return vars['QUESTFEEDBACK']


class MacroAVGToken(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        vars['AVGTOKEN'] = len(vars['ANSWERS']) / vars['SPOKENTIME']
        if vars['AVGTOKEN'] < 0.5:
            vars['TIMEFEEDBACK'] = "You should talk more."
        else:
            vars['TIMEFEEDBACK'] = "You should talk less."
        return vars['TIMEFEEDBACK']


class MacroTic(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        tokens = vars['ANSWERS'].split()
        vars['TIC'] = {}

        for token in tokens:
            if token in vars['TIC']:
                vars['TIC'][token] += 1
            else:
                vars['TIC'][token] = 1

        # Sort the word frequency dictionary by count
        sorted_words = sorted(vars['TIC'].items(), key=lambda x: x[1], reverse=True)

        # Extract the words at the desired positions
        vars['TICFEEDBACK'] = ""
        if len(sorted_words) >= 6:
            vars['TICFEEDBACK'] = f"{sorted_words[2][0]} {sorted_words[3][0]} {sorted_words[4][0]} {sorted_words[5][0]}"
        vars['TICFEEDBACK'] = "You should use less of " + vars['TICFEEDBACK']

        return vars['TICFEEDBACK']


class MacroAcknow(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if 'ANSWERS' not in vars:
            return
        if 'ACKNOW' not in vars:
            vars['ACKNOW'] = 0
        if vars['RESPONSE'] in vars['ANSWERS']:
            vars['ACKNOW'] += 1
        if vars['ACKNOW'] > 5:
            vars['EMPFEEDBACK'] = "You have successfully showed your attention to your partner."
        else:
            vars['EMPFEEDBACK'] = "You should show more attention to your partner. One good way is to acknowledge what " \
                                  "your partner said previously."
        return vars['EMPFEEDBACK']


class MacroAwkward(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        AWK = ["uh", "um", "like", "you know", "well", "so", "anyway", "actually", "i mean", "to be honest"]
        if 'USEDAWKWARD' not in vars:
            vars['USEDAWKWARD'] = 0
        for tran in AWK:
            if vars['RESPONSE'] in AWK:
                vars['USEDAWKWARD'] += tran
        if vars['USEDAWKWARD'] < 5:
            vars['AWKFEEDBACK'] = "You did not make many awkward transitions."
        else:
            vars['AWKFEEDBACK'] = "Try to avoid using uh, um, like, you know, and i mean."
        return vars['AWKFEEDBACK']


class MacroRecordAudio(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        # Define audio recording parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        RECORD_SECONDS = 5

        # Specify the directory to save the file
        SAVE_DIR = "C:/Users/Harry/PycharmProjects/conversational-ai/resources"
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

        # Specify the full path to the WAV file
        WAVE_OUTPUT_FILENAME = os.path.join(SAVE_DIR, "output.wav")

        # Create PyAudio object
        audio = pyaudio.PyAudio()

        # Start audio stream
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        print("Recording...")

        # Record audio data
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("Finished recording.")

        # Stop audio stream
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save audio data to WAV file
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        openai.api_key_path = 'C:/Users/Harry/OneDrive/Desktop/resource/chat_gpt_api_key.txt'
        audio_file = open("C:/Users/Harry/PycharmProjects/conversational-ai/resources/output.wav", "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        text = transcript['text']
        vars['CURRENT'] = text
        if 'ANSWERS' not in vars:
            vars['ANSWERS'] = text.lower()
            vars['SPOKENTIME'] = 15
        else:
            vars['ANSWERS'] = vars['ANSWERS'] + ' ' + text.lower()
            vars['SPOKENTIME'] = vars['SPOKENTIME'] + 15
        print(vars['CURRENT'])

        return True


class MacroRecordAudiolong(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        # Define audio recording parameters
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        CHUNK = 1024
        RECORD_SECONDS = 5

        # Specify the directory to save the file
        SAVE_DIR = "C:/Users/Harry/PycharmProjects/conversational-ai/resources"
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

        # Specify the full path to the WAV file
        WAVE_OUTPUT_FILENAME = os.path.join(SAVE_DIR, "output.wav")

        # Create PyAudio object
        audio = pyaudio.PyAudio()

        # Start audio stream
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        print("Recording...")

        # Record audio data
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)

        print("Finished recording.")

        # Stop audio stream
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save audio data to WAV file
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        openai.api_key_path = 'C:/Users/Harry/OneDrive/Desktop/resource/chat_gpt_api_key.txt'
        audio_file = open("C:/Users/Harry/PycharmProjects/conversational-ai/resources/output.wav", "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        text = transcript['text']
        vars['CURRENT'] = text
        if 'ANSWERS' not in vars:
            vars['ANSWERS'] = text.lower()
            vars['SPOKENTIME'] = 15
        else:
            vars['ANSWERS'] = vars['ANSWERS'] + ' ' + text.lower()
            vars['SPOKENTIME'] = vars['SPOKENTIME'] + 15
        print(vars['CURRENT'])
        print(vars['ANSWERS'])
        return True


def save(df: DialogueFlow, varfile: str):
    df.run()
    d = {k: v for k, v in df.vars().items() if not k.startswith('_')}
    pickle.dump(d, open(varfile, 'wb'))


def load(df: DialogueFlow, varfile: str):
    if os.path.isfile('C:/Users/Harry/PycharmProjects/conversational-ai/resources/visits.pkl'):
        d = pickle.load(open(varfile, 'rb'))
        df.vars().update(d)
    df.run()
    save(df, varfile)


def get_objective(vars: Dict[str, Any]):
    vars["OBJ"] = vars[V.objective.name][0]
    return vars[V.objective.name][0]


def get_time(vars: Dict[str, Any]):
    vars["TIME"] = vars[V.appointment_hours.name][0]
    return vars[V.appointment_hours.name][0]


macros = {
    "USERINPUT": MacroRecordAudio(),
    "USEREVAL": MacroRecordAudiolong(),
    "GTTS": MacrogTTS(),
    'GET_OBJECTIVE': MacroNLG(get_objective),
    'GET_TIME': MacroNLG(get_time),
    'SET_OBJECTIVE': MacroGPTJSON('What does the speaker wants to do? Answer in one of four options: haircut '
                                  'appointment, perm appointment, hair coloring appointment, error',
                                  {V.objective.name: ["haircut appointment"]}),
    'SET_TIME_CUT': MacroGPTJSON(
        'The available time for hair cut is Monday 10 AM, 1PM, 2PM, and Tuesday 2PM. Is the time the speaker wants available? Answer in yes or no.',
        {V.appointment_hours.name: ["yes"]}),
    'SET_TIME_COLOR': MacroGPTJSON(
        'The available time for hair coloring is Wednesday 10 AM, 11 AM, 1 PM, and Thursday 10 AM, 11 AM. Is the time the speaker wants available? Answer in yes or no.',
        {V.appointment_hours.name: ["yes"]}),
    'SET_TIME_PERM': MacroGPTJSON(
        'The available time for perm is Friday 10 AM, 11 AM, 1 PM, 2 PM, and Saturday 10 AM, 2PM. Is the time the speaker wants available? Answer in yes or no.',
        {V.appointment_hours.name: ["yes"]}),
    "QUEST": MacroNumQuestions(),
    "SPEED": MacroAVGToken(),
    "TIC": MacroTic(),
    "ACKNOW": MacroAcknow(),
    "ACKWARD": MacroAwkward(),
    "SIMPLENATEX": MacroNatex()

}

df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)
df.load_transitions(transitions_feedback)
df.load_transitions(transitions_evaluation)
df.knowledge_base().load_json_file('C:/Users/Harry/PycharmProjects/conversational-ai/resources/ontology_quiz3.json')
df.add_macros(macros)

if __name__ == '__main__':
    load(df, 'C:/Users/Harry/PycharmProjects/conversational-ai/resources/visits.pkl')


